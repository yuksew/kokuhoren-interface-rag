"""ハイブリッド検索: 全文検索（FTS5 trigram）とベクトル検索を順位融合（RRF）する。

usage: uv run --group rag python src/retrieve.py "受給者証番号の桁数" [--domain shogai] [--exchange J611] [--mode hybrid|fts|vector] [-k 10]
  前提: build_db.py → build_index.py
- 全文検索は「7131」「K122」のような番号や、項目名そのものの一致に強い。
- ベクトル検索は言い換え（「利用者の生まれた日」→ 生年月日）に強い。
- --domain / --exchange は絞り込み（必ず守る条件）として使う。
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RRF_K = 60
# 助詞・疑問の言い回しで区切って、全文検索の語を取り出す（trigram なので3文字以上の語だけ使う）
SPLIT = re.compile(r"[\s、。，,．.？?！!「」『』（）()\[\]【】・/:：]+|について|とは|には|では|での|への|から|まで|より|ですか|ますか|ください|教えて|何桁|何|どこ|どの|どう|いつ|[はがをにのでとやもかへ]")
MATRIX_Q = re.compile(r"必須|様式ごと|様式別|対応表|入力必須")
CODE = re.compile(r"(?<![0-9A-Za-z])[0-9A-Z]{4}(?![0-9A-Za-z])")


def nk(s) -> str:
    return unicodedata.normalize("NFKC", str(s or ""))


def fts_terms(q: str) -> list[str]:
    q = nk(q)
    terms = [t for t in SPLIT.split(q) if len(t) >= 3]
    terms += CODE.findall(q)
    return list(dict.fromkeys(terms))


class Retriever:
    def __init__(self, db: str = "db/interface_spec.sqlite", embedder: str = "ruri-v3-310m", embedder_obj=None):
        self.db_path = ROOT / db
        self.con = sqlite3.connect(self.db_path)
        self.con.row_factory = sqlite3.Row
        self.embedder_name = embedder
        self._df: dict[str, int] = {}
        self._emb = embedder_obj
        rows = self.con.execute(
            "SELECT c.chunk_id, c.kind, c.item_id, c.table_id, d.domain, t.table_kind FROM chunks c "
            "JOIN spec_tables t USING (table_id) JOIN documents d USING (doc_id) ORDER BY c.chunk_id").fetchall()
        self.meta = [dict(r) for r in rows]
        self.item_chunk = {m["item_id"]: m["chunk_id"] for m in self.meta if m["item_id"] is not None}
        self.vecs = np.load(self.db_path.parent / f"vectors.{embedder}.npy")
        assert len(self.vecs) == len(self.meta), "chunks と vectors の件数が合わない（build_index.py をやり直す）"
        self.ex_tables: dict[str, set[int]] = {}
        for r in self.con.execute("SELECT exchange_id, table_id FROM table_exchange_ids"):
            self.ex_tables.setdefault(r["exchange_id"], set()).add(r["table_id"])
        # インタフェース一覧の行: 識別番号 → その行（「J421 は何の情報？」に直接答える行）
        self.code_items: dict[str, list[int]] = {}
        for r in self.con.execute("SELECT iv.item_id, iv.value FROM item_values iv JOIN items i USING (item_id) "
                                  "JOIN spec_tables t USING (table_id) WHERE t.table_kind = 'interface_list' AND iv.column_name LIKE '%識別%'"):
            for code in CODE.findall(nk(r["value"]))[:1]:
                if r["item_id"] in self.item_chunk:
                    self.code_items.setdefault(code, []).append(self.item_chunk[r["item_id"]])

    @property
    def emb(self):
        if self._emb is None:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from llm.embedding import get_embedder
            self._emb = get_embedder(self.embedder_name)
        return self._emb

    def _allowed(self, domain: str | None, exchange: str | None) -> np.ndarray:
        ok = np.ones(len(self.meta), dtype=bool)
        if domain:
            ok &= np.array([m["domain"] == domain for m in self.meta])
        if exchange:
            ts = self.ex_tables.get(exchange, set())
            ok &= np.array([m["table_id"] in ts for m in self.meta])
        return ok

    def df(self, term: str) -> int:
        if term not in self._df:
            self._df[term] = self.con.execute("SELECT count(*) FROM items_fts WHERE items_fts MATCH ?",
                                              ('"' + term.replace('"', '""') + '"',)).fetchone()[0]
        return self._df[term]

    def fts(self, q: str, n: int = 50) -> list[int]:
        terms = fts_terms(q)
        # 「設定する」のようにほとんどの行にある語は手がかりにならないので外す（行の 3% 超）。全部外れたら一番まれな語だけ使う
        limit = len(self.item_chunk) * 0.03
        kept = [t for t in terms if self.df(t) <= limit]
        terms = kept or sorted(terms, key=self.df)[:1]
        if not terms:
            return []
        expr = " OR ".join('"' + t.replace('"', '""') + '"' for t in terms)
        rows = self.con.execute("SELECT rowid FROM items_fts WHERE items_fts MATCH ? ORDER BY rank LIMIT ?", (expr, n * 4)).fetchall()
        return [self.item_chunk[r["rowid"]] for r in rows if r["rowid"] in self.item_chunk]

    def vector(self, q: str, n: int = 50) -> list[int]:
        s = self.vecs @ self.emb.embed_query(q)
        return np.argsort(-s)[: n * 4].tolist()

    def codes(self, q: str) -> list[int]:
        """質問に既知の交換情報識別番号があれば、インタフェース一覧のその番号の行。"""
        return [c for code in CODE.findall(nk(q)) for c in self.code_items.get(code, [])]

    def search(self, q: str, k: int = 10, domain: str | None = None, exchange: str | None = None, mode: str = "hybrid",
               fts_weight: float = 1.0, use_codes: bool = True, matrix_weight: float = 0.5) -> list[dict]:
        ok = self._allowed(domain, exchange)
        lists = []
        if use_codes and mode != "vector":
            lists.append(("code", [c for c in self.codes(q) if ok[c]], 2.0))
        if mode in ("hybrid", "fts"):
            lists.append(("fts", [c for c in self.fts(q) if ok[c]][:50], fts_weight if mode == "hybrid" else 1.0))
        if mode in ("hybrid", "vector"):
            lists.append(("vector", [c for c in self.vector(q) if ok[c]][:50], 1.0))
        score: dict[int, float] = {}
        via: dict[int, list[str]] = {}
        # 必須対応表の行は同じ項目名が版（サービス提供年月）ごとに何十回も出てきて、項目の定義を押し出すので重みを下げる。
        # 質問が必須・様式について聞いているときは下げない。
        mx = 1.0 if MATRIX_Q.search(nk(q)) else matrix_weight
        for name, lst, w in lists:
            for rank, c in enumerate(lst):
                wm = mx if self.meta[c]["table_kind"] == "required_matrix" and self.meta[c]["kind"] == "item" else 1.0
                score[c] = score.get(c, 0.0) + w * wm / (RRF_K + rank + 1)
                via.setdefault(c, []).append(f"{name}#{rank + 1}")
        top = sorted(score, key=lambda c: -score[c])[:k]
        return [{**self.meta[c], "score": score[c], "via": via[c]} for c in top]

    def describe_table(self, table_id: int) -> str:
        return self.con.execute("SELECT text FROM chunks WHERE kind = 'table' AND table_id = ?", (table_id,)).fetchone()["text"]

    def describe(self, chunk_id: int) -> str:
        return self.con.execute("SELECT text FROM chunks WHERE chunk_id = ?", (chunk_id,)).fetchone()["text"]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--domain", choices=["kaigo", "shogai"])
    ap.add_argument("--exchange")
    ap.add_argument("--mode", default="hybrid", choices=["hybrid", "fts", "vector"])
    ap.add_argument("-k", type=int, default=10)
    args = ap.parse_args()
    r = Retriever()
    print("全文検索の語:", fts_terms(args.query))
    for i, x in enumerate(r.search(args.query, args.k, args.domain, args.exchange, args.mode), 1):
        first = r.describe(x["chunk_id"]).splitlines()
        print(f"{i:2d}. [{x['kind']}] {' / '.join(first[-4:])[:150]}  ({', '.join(x['via'])})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
