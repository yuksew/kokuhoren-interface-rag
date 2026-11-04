"""検索の評価: eval/questions.yaml の質問で、正解の行が上位に入るかを測る（API は使わない）。

usage: uv run --group rag python src/eval_retrieval.py [--out reports/retrieval_eval.md]
指標: hit@1・hit@5・hit@10（正解が上位 k 件に入った質問の割合）、MRR（最初の正解の順位の逆数の平均）
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from retrieve import Retriever  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
# (表示名, mode, fts_weight, use_codes, matrix_weight)
MODES = [("fts", "fts", 1.0, False, 1.0), ("vector", "vector", 1.0, False, 1.0), ("hybrid", "hybrid", 1.0, False, 1.0),
         ("hybrid+code", "hybrid", 1.0, True, 1.0), ("hybrid+code+matrix0.5", "hybrid", 1.0, True, 0.5)]


def norm(s) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", str(s or "")))


def gold_hits(r: Retriever, gold: list[dict]) -> tuple[set[int], set[int]]:
    """正解に当たる (item_id の集合, table_id の集合)。表単位の正解は、その表の行チャンクも表チャンクも正解とする。"""
    items, tables = set(), set()
    for g in gold:
        if "table" in g:
            sql = "SELECT table_id FROM spec_tables WHERE doc_id LIKE ? AND replace(ifnull(title,''),' ','') LIKE ?"
            ps = [g["doc"] + "%", "%" + norm(g["table"]) + "%"]
            if g.get("exchange"):
                sql += " AND table_id IN (SELECT table_id FROM table_exchange_ids WHERE exchange_id = ?)"
                ps.append(g["exchange"])
            tables |= {x[0] for x in r.con.execute(sql, ps)}
            continue
        for x in r.con.execute("SELECT i.item_id, i.name_full, i.page, t.table_kind FROM items i JOIN spec_tables t USING (table_id) "
                               "WHERE i.doc_id LIKE ?", (g["doc"] + "%",)):
            nf = norm(x["name_full"]).replace(">", "")
            if (norm(g["name"]).replace(">", "") in nf and (g.get("page") is None or x["page"] == g["page"])
                    and (g.get("table_kind") is None or x["table_kind"] == g["table_kind"])):
                items.add(x["item_id"])
    return items, tables


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reports/retrieval_eval.md")
    args = ap.parse_args()
    qs = yaml.safe_load((ROOT / "eval" / "questions.yaml").read_text(encoding="utf-8"))
    r = Retriever()
    res = defaultdict(list)  # mode -> [rank or None]
    detail = []
    for q in qs:
        if not q.get("gold"):
            continue   # 正解の行が無い問（範囲外の質問・算定ルール資料の質問）は回答の評価だけ
        gi, gt = gold_hits(r, q["gold"])
        assert gi or gt, f"正解が DB に見つからない: {q['q']}"
        row = {"q": q["q"], "kind": q["kind"]}
        for m, mode, w, uc, mw in MODES:
            hits = r.search(q["q"], k=10, domain=q.get("domain"), mode=mode, fts_weight=w, use_codes=uc, matrix_weight=mw)
            rank = next((i + 1 for i, h in enumerate(hits)
                         if (h["item_id"] in gi) or (h["table_id"] in gt)), None)
            res[m].append((q["kind"], rank))
            row[m] = rank
        detail.append(row)

    def summary(ranks):
        n = len(ranks)
        f = lambda k: sum(1 for x in ranks if x and x <= k) / n
        mrr = sum(1 / x for x in ranks if x) / n
        return f"{f(1):.2f} | {f(5):.2f} | {f(10):.2f} | {mrr:.2f}"

    lines = [f"# 検索の評価（{len(qs)} 問、API 不使用）", "",
             f"埋め込み: {r.embedder_name} ／ 全文検索: FTS5 trigram ／ 融合: RRF (k={60})", "",
             "| 方式 | hit@1 | hit@5 | hit@10 | MRR |", "|---|--:|--:|--:|--:|"]
    for m, *_ in MODES:
        lines.append(f"| {m} | {summary([x for _, x in res[m]])} |")
    names = [m for m, *_ in MODES]
    lines += ["", "質問の種類別の hit@5", "", "| 種類 | 問数 | " + " | ".join(names) + " |", "|---|--:|" + "--:|" * len(names)]
    for kind in sorted({q["kind"] for q in qs}):
        cells = []
        for m in names:
            rs = [x for k_, x in res[m] if k_ == kind]
            cells.append(f"{sum(1 for x in rs if x and x <= 5)}/{len(rs)}")
        lines.append(f"| {kind} | {len([q for q in qs if q['kind'] == kind])} | " + " | ".join(cells) + " |")
    lines += ["", "質問ごとの正解の順位（— は上位10件に無し）", "", "| 質問 | 種類 | " + " | ".join(names) + " |", "|---|---|" + "--:|" * len(names)]
    for d in detail:
        lines.append(f"| {d['q']} | {d['kind']} | " + " | ".join(str(d[m] or "—") for m in names) + " |")
    out = "\n".join(lines) + "\n"
    (ROOT / args.out).write_text(out, encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
