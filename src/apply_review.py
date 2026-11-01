"""確認画面（review_app.py）の判定を採用版に反映し、確定版を作る。何度実行しても同じ結果になる。

usage: uv run python src/apply_review.py [--run prod1-png-post]
出力:
  out/{run}-reviewed/{doc_id}_p{page}.json   確定版（人が直した箇所は _fixes に by: "human" で記録）
  out/{run}-reviewed/logical_tables.json     ページをまたぐ表を結合した論理的な表
  reports/review_status.{run}.csv            キューの各項目の判定（未判定・保留も含む）
未判定・保留の項目は Haiku のまま（採用版のまま）残す。
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pagemeta import doc_profile  # noqa: E402
from postprocess import build_logical  # noqa: E402
from review_core import ROOT, apply_page, load_decisions, load_page, load_queue, paths  # noqa: E402

ACTION_LABEL = {None: "未判定", "haiku": "Haiku", "sonnet": "Sonnet", "edit": "修正値", "delete": "削除",
                "manual": "セルを個別に修正", "hold": "保留"}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="prod1-png-post")
    args = ap.parse_args()
    P = paths(args.run)
    queue, dec = load_queue(args.run), load_decisions(args.run)
    by_page = defaultdict(list)
    for q in queue:
        by_page[(q["doc"], q["page"])].append(q)
    cell_pages = {(k.split("|")[0], int(k.split("|")[1])) for k in dec["cells"]}

    out = P["reviewed"]
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    pages_by_doc, profiles = defaultdict(list), {}
    stats = Counter()
    for f in sorted(P["adopted"].glob("*_p*.json")):
        body = json.loads(f.read_text(encoding="utf-8"))
        doc, page = body["doc_id"], body["page"]
        key = (doc, page)
        if key in by_page or key in cell_pages:
            adopted, sonnet = load_page(args.run, doc, page)
            body = apply_page(adopted, sonnet, by_page.get(key, []), dec, final=True)
            stats["pages_changed"] += 1
        (out / f.name).write_text(json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8")
        if doc not in profiles:
            dom = "kaigo" if doc.startswith("kaigo") else "shogai"
            profiles[doc] = doc_profile(ROOT / "sources" / "raw" / dom / f"{doc}.pdf")
        pages_by_doc[doc].append((page, {k: v for k, v in body.items() if k not in ("domain", "doc_id", "page")}))
        stats["pages"] += 1
        stats["human_fixes"] += sum(1 for t in body.get("tables") or [] for x in [t] + (t.get("items") or [])
                                    for fx in x.get("_fixes") or [] if fx.get("by") == "human")
    for v in pages_by_doc.values():
        v.sort(key=lambda x: x[0])
    logical, _ = build_logical(pages_by_doc, profiles)
    (out / "logical_tables.json").write_text(json.dumps(logical, ensure_ascii=False, indent=1), encoding="utf-8")

    acts = Counter()
    sf = ROOT / "reports" / f"review_status.{args.run}.csv"
    with sf.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["文書", "PDFページ", "表", "項番", "列", "判定", "Haiku", "Sonnet", "状態", "入力した値", "判定日時"])
        for q in queue:
            d = dec["items"].get(q["id"]) or {}
            a = d.get("action")
            acts[ACTION_LABEL[a]] += 1
            w.writerow([q["doc"], q["page"], "" if q["table"] is None else q["table"] + 1, q["no"], q["field"], q["verdict"],
                        q["haiku"], q["sonnet"], ACTION_LABEL[a], d.get("value", ""), d.get("at", "")])
    stale = [k for k in dec["items"] if k not in {q["id"] for q in queue}]
    print(f"キュー {len(queue)} 件: " + "、".join(f"{k} {v}" for k, v in acts.most_common()))
    print(f"セルの個別修正 {len(dec['cells'])} 件 / 人の修正記録 {stats['human_fixes']} 件 / 反映したページ {stats['pages_changed']}")
    if stale:
        print(f"注意: キューに無くなった判定が {len(stale)} 件あります（採用版を作り直した影響）。反映していません。")
    print(f"→ {out.relative_to(ROOT)}（{stats['pages']}ページ、論理表 {len(logical)}）, {sf.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
