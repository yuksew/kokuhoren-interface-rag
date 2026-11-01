"""2つの run（改修前・改修後）を、共通のページについて比べる。

usage: uv run python src/compare_runs.py BEFORE_RUN AFTER_RUN [--out reports/xxx.md]
例:    uv run python src/compare_runs.py pilot-png-post rerun1-png-post
前提: 両方の run で validate.py を実行済み（validation.json がある）。
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def norm(s) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", str(s or ""))).replace("◯", "○").replace("〇", "○")


def page_text(res: dict) -> str:
    """行の切り方に左右されない比較用に、ページ内の全セルを順に連結した文字列。"""
    out = []
    for t in res.get("tables") or []:
        for it in t.get("items") or []:
            out += [" ".join(it.get("name_path") or []), it.get("type"), it.get("length_raw") or it.get("length"),
                    it.get("content"), it.get("required"), it.get("note")]
            out += [x.get("value") for x in it.get("required_by") or []]
            out += [x.get("value") for x in it.get("cells") or []]
    return norm("".join(str(x) for x in out if x is not None))


def load(run: str):
    v = json.loads((ROOT / "out" / run / "validation.json").read_text(encoding="utf-8"))
    return v, {p["key"]: p for p in v["pages"]}


def metrics(run: str, keys: list[str], models: list[str]) -> dict:
    v, pages = load(run)
    m_out: dict = {}
    for m in models:
        c = Counter()
        for k in keys:
            p = pages.get(k)
            if not p or m not in p["by_model"]:
                c["missing"] += 1
                continue
            iss = p["by_model"][m]["issues"]
            c["pages"] += 1
            c["items"] += p["by_model"][m].get("stats", {}).get("items", 0) or 0
            c["omission_pages"] += any(i["msg"].startswith("[省略]") for i in iss)
            c["col_warn_tables"] += sum(1 for i in iss if i["msg"].startswith("[列]"))
            c["bad_required_values"] += sum(1 for i in iss if "の値が想定外" in i["msg"])
            c["text_missing"] += p["by_model"][m].get("stats", {}).get("text_missing", 0) or 0
            c["text_checked"] += p["by_model"][m].get("stats", {}).get("text_checked", 0) or 0
            c["name_partial"] += p["by_model"][m].get("stats", {}).get("name_partial", 0) or 0
            meta = p["by_model"][m]["meta"]
            c["cost_batch_usd_x1000"] += round(1000 * (meta.get("cost_usd_batch") or 0))
            c["output_tokens"] += meta["usage"]["output_tokens"]
        m_out[m] = c
    # モデル間
    sims, rows, diffs = [], 0, 0
    for k in keys:
        p = pages.get(k)
        if not p:
            continue
        rows += sum(1 for d in p.get("diffs") or [] if d["field"] == "row")
        diffs += sum(1 for d in p.get("diffs") or [] if d["field"] not in ("tables", "row"))
        r = []
        for m in models:
            f = ROOT / "out" / run / m / f"{k}.json"
            r.append(json.loads(f.read_text(encoding="utf-8"))["result"] if f.exists() else None)
        if all(r):
            a, b = page_text(r[0]), page_text(r[1])
            if a and b:
                sims.append(difflib.SequenceMatcher(None, a, b, autojunk=False).ratio())
    return {"by_model": m_out, "sim": sims, "row_only": rows, "diff_cells": diffs}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("before")
    ap.add_argument("after")
    ap.add_argument("--groups", default=None, help="config yaml（pages にコメントで区切ったグループがある）")
    args = ap.parse_args()
    _, after_pages = load(args.after)
    keys = sorted(after_pages)
    models = load(args.after)[0]["models"]
    B, A = metrics(args.before, keys, models), metrics(args.after, keys, models)

    def sim_line(s):
        if not s:
            return "-"
        s = sorted(s)
        return f"中央値 {s[len(s) // 2]:.3f} / 0.98以上 {sum(x >= 0.98 for x in s)} / 0.9以上 {sum(x >= 0.9 for x in s)} / 0.8未満 {sum(x < 0.8 for x in s)}（{len(s)}ページ）"

    print(f"対象 {len(keys)} ページ: {args.before} → {args.after}\n")
    print("| 指標 | モデル | 改修前 | 改修後 |\n|---|---|--:|--:|")
    for k in ["items", "omission_pages", "col_warn_tables", "bad_required_values", "text_missing", "text_checked",
              "name_partial", "output_tokens", "cost_batch_usd_x1000"]:
        for m in models:
            print(f"| {k} | {m} | {B['by_model'][m][k]} | {A['by_model'][m][k]} |")
    print(f"| 片方にしかない行 | - | {B['row_only']} | {A['row_only']} |")
    print(f"| 食い違いセル | - | {B['diff_cells']} | {A['diff_cells']} |")
    print(f"\nページ全体の文字一致率（モデル間）\n- 改修前: {sim_line(B['sim'])}\n- 改修後: {sim_line(A['sim'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
