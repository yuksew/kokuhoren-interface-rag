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
# 質問の向き: 仕様書（CSV の形式）か、算定ルール（いつ・何を算定・請求できるか）か
SPEC_Q = re.compile(r"桁|属性|項目|レコード|形式|CSV|交換情報|識別番号|設定|フォーマット|インタフェース")
# 古い様式（「サービス提供年月が平成18年3月以前の場合」など）を聞いている質問
OLD_Q = re.compile(r"平成|以前|旧様式|昔|過去|H[0-9]{1,2}")
# 事業所向けでない編（自治体・生活保護・合併）と、それを聞いている質問。
# これらの編には、事業所向けの編と同じ定義の項目（明細書・給付管理票の生保版など）が丸ごと載っていて、事業所の質問で上位を埋める
OTHER_VOL = re.compile(r"都道府県編|保険者編|生保単独編|市町村合併編|市町村編")
OTHER_Q = re.compile(r"都道府県|(?<!被)保険者|市町村|自治体|生保|生活保護|合併|異動連絡|台帳")
RULE_Q = re.compile(r"算定|加算|減算|単位|請求|時間|回数|何回|できる|可能|留意|告示|Q&A|サービスコード|要件|基準|間隔|上限|最大|日割")
VALUE = re.compile(r"^([0-9A-Z]{1,6})\s*[:：]")
SHORT = re.compile(r"(?<![0-9A-Za-z])((?=[0-9A-Z]{2,3}(?![0-9A-Za-z]))[0-9]*[A-Z][0-9A-Z]*)(?![0-9A-Za-z])")
CODE = re.compile(r"(?<![0-9A-Za-z])[0-9A-Z]{4}(?![0-9A-Za-z])")
# サービスコード（種類2桁＋項目4桁。「11 4845」「114845」）
LIMIT = re.compile(r"整数部\s*上?\s*(\d+)\s*桁\s*[、,+＋]?\s*小数部\s*下?\s*(\d+)\s*桁")
SVC = re.compile(r"(?<![0-9A-Za-z])([0-9]{2})\s?([0-9A-Z]{4})(?![0-9A-Za-z])")


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
            "SELECT c.chunk_id, c.kind, c.item_id, c.table_id, c.doc_id, c.page, COALESCE(d.domain, rd.domain) AS domain, "
            "t.table_kind, rd.category AS rule_category FROM chunks c "
            "LEFT JOIN spec_tables t ON t.table_id = c.table_id LEFT JOIN documents d ON d.doc_id = c.doc_id "
            f"LEFT JOIN {'rule_docs' if self._has('rule_docs') else '(SELECT NULL AS doc_id, NULL AS domain, NULL AS category)'} rd "
            "ON rd.doc_id = c.doc_id ORDER BY c.chunk_id").fetchall()
        self.meta = [dict(r) for r in rows]
        self.item_chunk = {m["item_id"]: m["chunk_id"] for m in self.meta if m["item_id"] is not None}
        self.vecs = np.load(self.db_path.parent / f"vectors.{embedder}.npy")
        assert len(self.vecs) == len(self.meta), "chunks と vectors の件数が合わない（build_index.py をやり直す）"
        # 古い様式の表（表題に「〜以前」）。同じ項目が様式の世代ごとに出てきて現行の表を押し出すので、重みを下げる
        self.other_docs = {r["doc_id"] for r in self.con.execute("SELECT doc_id, volume FROM documents") if OTHER_VOL.search(r["volume"] or "")}
        self.old_tables = {r["table_id"] for r in self.con.execute("SELECT table_id FROM spec_tables WHERE title LIKE '%以前%'")}
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
        # コード一覧の値: 「A4:訪問型サービス（独自／定額）」のような行頭のコード → その行。
        # 「A4」のような2文字は全文検索（3文字以上）でもベクトル検索でも引けないので、ここで直接引く
        self.value_items: dict[str, list[int]] = {}
        for r in self.con.execute("SELECT item_id, content FROM items WHERE content LIKE '%:%' OR content LIKE '%：%'"):
            for ln in nk(r["content"]).splitlines():
                m = VALUE.match(ln.strip())
                if m and r["item_id"] in self.item_chunk:
                    lst = self.value_items.setdefault(m.group(1), [])
                    if self.item_chunk[r["item_id"]] not in lst:
                        lst.append(self.item_chunk[r["item_id"]])

        # サービスコード → そのコードの行を含むチャンク
        self.svc_ranges = [(m["chunk_id"], r["sc_from"], r["sc_to"]) for m, r in zip(self.meta, self.con.execute(
            "SELECT sc_from, sc_to FROM chunks ORDER BY chunk_id")) if m["kind"] == "svc"]

    def _has(self, table: str) -> bool:
        return self.con.execute("SELECT 1 FROM sqlite_master WHERE name = ?", (table,)).fetchone() is not None

    def svc_chunks(self, q: str) -> list[int]:
        if not self.svc_ranges:
            return []
        out = []
        for kind, item in SVC.findall(nk(q)):
            for (sc_id,) in self.con.execute("SELECT sc_id FROM service_codes WHERE code = ?", (kind + item,)):
                out += [c for c, a, b in self.svc_ranges if a <= sc_id <= b]
        return list(dict.fromkeys(out))

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
            self._df[term] = sum(self.con.execute(f"SELECT count(*) FROM {t} WHERE {t} MATCH ?",
                                                  ('"' + term.replace('"', '""') + '"',)).fetchone()[0]
                                 for t in ("items_fts", "prose_fts"))
        return self._df[term]

    def fts(self, q: str, n: int = 50) -> list[int]:
        terms = fts_terms(q)
        # 「設定する」のようにほとんどの行にある語は手がかりにならないので外す（行の 3% 超）。全部外れたら一番まれな語だけ使う
        limit = len(self.meta) * 0.03
        kept = [t for t in terms if self.df(t) <= limit]
        terms = kept or sorted(terms, key=self.df)[:1]
        if not terms:
            return []
        expr = " OR ".join('"' + t.replace('"', '""') + '"' for t in terms)
        rows = self.con.execute("SELECT rowid FROM items_fts WHERE items_fts MATCH ? ORDER BY rank LIMIT ?", (expr, n * 4)).fetchall()
        items = [self.item_chunk[r["rowid"]] for r in rows if r["rowid"] in self.item_chunk]
        prose = [r["rowid"] for r in self.con.execute("SELECT rowid FROM prose_fts WHERE prose_fts MATCH ? ORDER BY rank LIMIT ?",
                                                      (expr, n)).fetchall()]
        # 行と文章を交互に並べる（どちらかが他方を押し出さないように）
        out = []
        for i in range(max(len(items), len(prose))):
            out += [x for x in (items[i] if i < len(items) else None, prose[i] if i < len(prose) else None) if x is not None]
        return out

    def vector(self, q: str, n: int = 50) -> list[int]:
        s = self.vecs @ self.emb.embed_query(q)
        return np.argsort(-s)[: n * 4].tolist()

    def codes(self, q: str) -> list[int]:
        """質問に既知の交換情報識別番号があればインタフェース一覧のその番号の行、
        英字を含む短いコード（A4 など）があればコード一覧でそのコードを定義している行。"""
        q = nk(q)
        out = [c for code in CODE.findall(q) for c in self.code_items.get(code, [])]
        out += [c for code in SHORT.findall(q) for c in self.value_items.get(code, [])[:10]]
        out += self.svc_chunks(q)
        return list(dict.fromkeys(out))

    def search(self, q: str, k: int = 10, domain: str | None = None, exchange: str | None = None, mode: str = "hybrid",
               fts_weight: float = 1.0, use_codes: bool = True, matrix_weight: float = 0.5, rule_weight: float = 0.5,
               old_weight: float = 0.3, other_weight: float = 0.3) -> list[dict]:
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
        # 仕様書の形式だけを聞いている質問では、算定ルール資料（数が多い）が仕様書の行を押し出すので重みを下げる
        rw = rule_weight if SPEC_Q.search(nk(q)) and not RULE_Q.search(nk(q)) else 1.0
        ow = 1.0 if OLD_Q.search(nk(q)) else old_weight
        vw = 1.0 if OTHER_Q.search(nk(q)) else other_weight
        for name, lst, w in lists:
            for rank, c in enumerate(lst):
                wm = mx if self.meta[c]["table_kind"] == "required_matrix" and self.meta[c]["kind"] == "item" else 1.0
                if self.meta[c]["kind"] in ("rule", "svc"):
                    wm = rw
                if self.meta[c]["table_id"] in self.old_tables:
                    wm *= ow
                if self.meta[c]["doc_id"] in self.other_docs:
                    wm *= vw
                score[c] = score.get(c, 0.0) + w * wm / (RRF_K + rank + 1)
                via.setdefault(c, []).append(f"{name}#{rank + 1}")
        top = sorted(score, key=lambda c: -score[c])[:k]
        return [{**self.meta[c], "score": score[c], "via": via[c]} for c in top]

    def search_multi(self, queries: list[str], k: int = 10, keep: int | None = None, **kw) -> list[dict]:
        """複数の検索文（元の質問＋言い換え）の結果を、順位で融合する（RRF）。1つ目（元の質問）を少し重くする。
        言い換えがずれても元の質問で引けていたものを失わないよう、元の質問の上位 keep 件（既定 k の半分）は必ず残す。"""
        if len(queries) <= 1:
            return self.search(queries[0], k=k, **kw)
        keep = k // 2 if keep is None else keep
        first = self.search(queries[0], k=50, **kw)
        score: dict[int, float] = {}
        via: dict[int, list[str]] = {}
        for qi, q in enumerate(queries):
            w = 1.2 if qi == 0 else 1.0
            for rank, h in enumerate(first if qi == 0 else self.search(q, k=50, **kw)):
                c = h["chunk_id"]
                score[c] = score.get(c, 0.0) + w / (RRF_K + rank + 1)
                via.setdefault(c, []).append(f"q{qi}#{rank + 1}")
        top = [h["chunk_id"] for h in first[:keep]]
        top += [c for c in sorted(score, key=lambda c: -score[c]) if c not in top][: k - len(top)]
        top.sort(key=lambda c: -score[c])
        return [{**self.meta[c], "score": score[c], "via": via[c]} for c in top]

    def info_names(self) -> dict[tuple[str, str], str]:
        """(domain, 交換情報識別番号) → 情報名（インタフェース一覧から）"""
        if not hasattr(self, "_info"):
            self._info = {}
            for r in self.con.execute("SELECT d.domain, i.name, iv.value FROM item_values iv JOIN items i USING (item_id) "
                                      "JOIN spec_tables t USING (table_id) JOIN documents d ON d.doc_id = t.doc_id "
                                      "WHERE t.table_kind = 'interface_list' AND iv.column_name LIKE '%識別%'"):
                m = CODE.search(nk(r["value"]))
                if m and r["name"]:
                    self._info.setdefault((r["domain"], m.group(0)), re.sub(r"\s*※\s*\S+", "", nk(r["name"])).strip())
        return self._info

    def exchange_overview(self, queries: list[str], hits: list[dict], domain: str | None, max_ids: int = 6) -> str | None:
        """「CSV の構造は？」のような質問用に、関係しそうな交換情報（識別番号・情報名）と、そのレコード表の一覧を作る。
        候補: インタフェース一覧の行（1行 = 1つの交換情報）を、質問と言い換えの検索文との意味の近さで並べた上位。
        同じレコード構成の交換情報（例: 7131 と 7143）は1行にまとめる。"""
        info = self.info_names()
        rev = {c: code for code, cs in self.code_items.items() for c in cs}
        cand = [c for c in rev if domain is None or self.meta[c]["domain"] == domain]
        if not cand:
            return None
        qv = np.stack([self.emb.embed_query(q) for q in queries])
        sims = (self.vecs[cand] @ qv.T).max(axis=1)
        ids: list[str] = []
        for i in np.argsort(-sims):
            ex = rev[cand[i]]
            if ex not in ids:
                ids.append(ex)
            if len(ids) >= max_ids * 2:
                break
        groups: dict[tuple, list[str]] = {}
        heads: dict[tuple, str] = {}
        for ex in ids:
            rows = self.con.execute(
                "SELECT DISTINCT t.title, t.page_from, d.domain, d.volume, d.edition FROM table_exchange_ids x JOIN spec_tables t USING (table_id) "
                "JOIN documents d USING (doc_id) WHERE x.exchange_id = ? AND t.table_kind = 'record_layout'"
                + (" AND d.domain = ?" if domain else "") + " ORDER BY d.domain, t.page_from",
                (ex, domain) if domain else (ex,)).fetchall()
            if not rows:
                continue
            recs = []
            for r in rows:
                t = nk(r["title"] or "（表題なし）").strip(" ・")
                m = re.match(r"(.*?レコード(?:\(複数レコード\))?)", t)
                recs.append(m.group(1) if m else t.splitlines()[0][:40])
            key = (rows[0]["domain"], tuple(dict.fromkeys(recs)))
            groups.setdefault(key, []).append(ex)
            heads.setdefault(key, f"{rows[0]['volume']} {rows[0]['edition']} PDF {rows[0]['page_from']}ページ〜")
            if len(groups) >= max_ids:
                break
        if not groups:
            return None
        lines = []
        for key, exs in groups.items():
            names = "／".join(dict.fromkeys(info.get((key[0], ex), "（情報名不明）") for ex in exs))
            lines.append(f"- {'・'.join(exs)} {names}（{heads[key]}）: " + " → ".join(key[1]))
        return ("交換情報ごとのレコード構成（インタフェース一覧とレコード表の表題から機械的に作成。質問に近い順。"
                "各交換情報は、共通のコントロールレコード・エンドレコードの間に、これらのデータレコードを入れる）:\n" + "\n".join(lines))

    def numeric_limits(self, queries: list[str], domain: str | None, max_items: int = 8) -> str | None:
        """「最大何時間？」「1000時間を超えたら？」のような質問用に、桁の決まった数値項目と、そこに設定できる最大値を並べる。
        候補: 内容に「整数部N桁＋小数部M桁」と書かれた項目。質問と言い換えの検索文との意味の近さで並べ、
        同じ項目名・同じ桁の行（版ちがい）は1つにまとめる。"""
        if not hasattr(self, "_limits"):
            self._limits = []
            rows = self.con.execute("SELECT item_id, domain, volume, edition, page, table_title, name_full, type, length_raw, content "
                                    "FROM v_items WHERE content LIKE '%整数部%'").fetchall()
            for r in rows:
                m = LIMIT.search(nk(r["content"]))
                if m and r["item_id"] in self.item_chunk:
                    self._limits.append((self.item_chunk[r["item_id"]], dict(r), int(m.group(1)), int(m.group(2))))
        cand = [x for x in self._limits if domain is None or x[1]["domain"] == domain]
        if not cand:
            return None
        qv = np.stack([self.emb.embed_query(q) for q in queries])
        sims = (self.vecs[[x[0] for x in cand]] @ qv.T).max(axis=1)
        # 質問に「1000時間」のような数値と単位があれば、その値を設定できない（最大値がその値の少し下の）項目を先に出す
        asked = [(float(n.replace(",", "")), u) for n, u in re.findall(r"([0-9][0-9,]*(?:\.[0-9]+)?)\s*(時間|円|日|回|%)", nk(queries[0]))]
        for n, u in asked:
            below = {i: 10 ** a - 10 ** -b for i, (c, r, a, b) in enumerate(cand) if u in nk(r["content"]) and 10 ** a - 10 ** -b < n}
            top = max(below.values(), default=None)
            for i, mx in below.items():
                if mx == top:
                    sims[i] += 1.0
        lines, seen = [], set()
        for i in np.argsort(-sims):
            c, r, a, b = cand[i]
            key = (r["domain"], nk(r["name_full"] or ""), a, b)
            if key in seen:
                continue
            seen.add(key)
            mx = "9" * a + ("." + "9" * b if b else "")
            first = nk(r["content"]).replace("\n", " ")[:120]
            lines.append(f"- {nk(r['name_full'] or '（項目名なし）')}（{nk(r['table_title'] or '表題なし').splitlines()[0][:40]}、"
                         f"{r['volume']} {r['edition']} PDF p{r['page']}）: 属性 {r['type'] or '-'} / 桁数 {r['length_raw'] or '-'} / "
                         f"整数部{a}桁＋小数部{b}桁 → 設定できる最大値 {mx} / 内容「{first}」")
            if len(lines) >= max_items:
                break
        return ("桁の決まった数値項目と、設定できる最大値（項目の内容の「整数部N桁＋小数部M桁」から機械的に計算。質問に近い順。"
                "最大値を超える値はこの項目に設定できない）:\n" + "\n".join(lines))

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
