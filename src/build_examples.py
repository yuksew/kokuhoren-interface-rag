"""書き起こした「設定例」を採用して、DB の examples テーブルと CSV にする。

usage: uv run python src/build_examples.py [--config config/examples.yaml] [--db db/interface_spec.sqlite]
  前提: transcribe_examples.py で out/examples/{doc}/{haiku,sonnet}/p*.json を作ってある。build_db.py の後に実行する
        （build_db.py は DB を作り直すので、そのたびにこれもやり直す）。この後に build_index.py。
出力:
  DB の examples テーブル                    事例1件1行（表は JSON）
  out/examples/{doc}/examples.json         採用した事例（頁をまたぐ事例はつないである）
  out/examples/{doc}/examples.csv          事例1件1行（入力と説明）
  out/examples/{doc}/example_cells.csv     表のセル1つ1行（事例・表・行・列・値。横にまたがるセルは span_to にまたがる最後の列）
  out/examples/{doc}/examples.md           人が読む用の一覧
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from transcribe_examples import parse_pages  # noqa: E402


def load_examples(doc: str, pages: list[int], base: str, use: dict[str, str], notes: dict[str, str] | None = None,
                  spans: dict[str, list[dict]] | None = None) -> list[dict]:
    out: list[dict] = []
    section = None
    for p in pages:
        res = {m: json.loads((ROOT / "out" / "examples" / doc / m / f"p{p}.json").read_text(encoding="utf-8"))["result"]
               for m in {base, *use.values()}}
        r = res[base]
        section = r["heading"] or section
        for i, e in enumerate(r["examples"]):
            m = use.get(f"{p}#{i}", base)
            e = res[m]["examples"][i]
            # No も事例名も無い枠は、前の事例の続き（例: 紙様式記載の頁と、インタフェース設定の頁に分かれている）
            if out and not e["no"] and not e["title"] and not e["provisions"]:
                prev = out[-1]
                prev["tables"] += e["tables"]
                prev["explanation"] = "\n".join(x for x in (prev["explanation"], e["explanation"]) if x) or None
                prev["page_to"] = p
                prev["models"].append(f"p{p}:{m}")
                continue
            out.append({"doc_id": doc, "page_from": p, "page_to": p, "printed_page": r["printed_page"], "section": section,
                        "no": e["no"], "title": e["title"], "provision_text": e["provision_text"], "provisions": e["provisions"],
                        "timeline_note": e["timeline_note"], "tables": e["tables"], "explanation": e["explanation"],
                        "page_note": r["other_text"] if i == 0 else None, "models": [f"p{p}:{m}"],
                        "note": (notes or {}).get(f"{p}#{i}"), "spans": (spans or {}).get(f"{p}#{i}", [])})
    return out


def cell(v) -> str:
    return "" if v is None else str(v)


def render_text(e: dict, head: str) -> str:
    """事例1件を、検索と回答に渡す文章にする。"""
    pages = f"PDF p{e['page_from']}" + (f"〜{e['page_to']}" if e["page_to"] != e["page_from"] else "")
    lines = [head, f"設定例: {e['section'] or ''} No.{e['no'] or '-'} {e['title'] or ''}（{pages}、印刷 {e['printed_page'] or '-'}）"]
    if e["provisions"]:
        lines.append("実際の提供: " + "、".join(
            " ".join(x for x in (p["label"], f"（{p['staff']}）" if p["staff"] else "", p["day"] or "",
                                 f"{p['start'] or '?'}〜{p['end'] or '?'}") if x) for p in e["provisions"]))
    elif e["provision_text"]:
        lines.append("実際の提供: " + e["provision_text"].replace("\n", " "))
    if e["timeline_note"]:
        lines.append("図の注記: " + e["timeline_note"])
    # 説明は表より前に置く（表が長い事例でも、埋め込みの長さの上限で説明が切れないように）
    if e["explanation"]:
        lines.append("説明: " + e["explanation"])
    for t in e["tables"]:
        lines.append(f"表「{t['caption'] or '（見出しなし）'}」（{'入力' if t['role'] == 'input' else 'インタフェース設定'}）:")
        if t["fields"]:
            lines.append("  " + " / ".join(f"{f['label']} {cell(f['value'])}{f['unit'] or ''}" for f in t["fields"]))
        if t["columns"]:
            lines.append("  列: " + " | ".join(t["columns"]))
        lines += ["  " + " | ".join(cell(v) for v in r) for r in t["rows"]]
    if e["page_note"]:
        lines.append("頁の注記: " + e["page_note"])
    if e["note"]:
        lines.append("書き起こしの注記: " + e["note"])
    return "\n".join(lines)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/examples.yaml")
    ap.add_argument("--db", default="db/interface_spec.sqlite")
    args = ap.parse_args()
    cfg = yaml.safe_load((ROOT / args.config).read_text(encoding="utf-8"))
    con = sqlite3.connect(ROOT / args.db)
    con.row_factory = sqlite3.Row
    con.executescript("""
DROP TABLE IF EXISTS examples;
CREATE TABLE examples (example_id INTEGER PRIMARY KEY, doc_id TEXT NOT NULL, page_from INTEGER, page_to INTEGER, printed_page TEXT,
                       section TEXT, no TEXT, title TEXT, provision_text TEXT, provisions TEXT, timeline_note TEXT,
                       tables TEXT, explanation TEXT, page_note TEXT, models TEXT, text TEXT NOT NULL);
""")
    eid = 0
    for d in cfg["docs"]:
        doc = con.execute("SELECT * FROM documents WHERE doc_id = ?", (d["doc"],)).fetchone()
        head = f"{'障害福祉' if doc['domain'] == 'shogai' else '介護保険'} インタフェース仕様書 {doc['volume']} {doc['edition']}"
        exs = load_examples(d["doc"], parse_pages(d["pages"]), d["base"], d.get("use") or {}, d.get("notes"), d.get("spans"))
        out_dir = ROOT / "out" / "examples" / d["doc"]
        md = [f"# 設定例: {head}", "", f"{len(exs)} 件。`src/build_examples.py` が作る（手で直さない）。", ""]
        with (out_dir / "examples.csv").open("w", encoding="utf-8-sig", newline="") as f1, \
             (out_dir / "example_cells.csv").open("w", encoding="utf-8-sig", newline="") as f2:
            w1, w2 = csv.writer(f1), csv.writer(f2)
            w1.writerow(["example_id", "section", "no", "title", "pdf_page_from", "pdf_page_to", "printed_page",
                         "provisions", "explanation", "note", "url"])
            w2.writerow(["example_id", "table_no", "role", "caption", "row_no", "column", "value", "span_to"])
            for e in exs:
                eid += 1
                e["example_id"] = eid
                text = render_text(e, head)
                con.execute("INSERT INTO examples VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            (eid, e["doc_id"], e["page_from"], e["page_to"], e["printed_page"], e["section"], e["no"], e["title"],
                             e["provision_text"], json.dumps(e["provisions"], ensure_ascii=False), e["timeline_note"],
                             json.dumps(e["tables"], ensure_ascii=False), e["explanation"], e["page_note"],
                             ",".join(e["models"]), text))
                prov = "、".join(f"{p['label']}{'（' + p['staff'] + '）' if p['staff'] else ''} {p['start'] or '?'}〜{p['end'] or '?'}"
                                for p in e["provisions"]) or (e["provision_text"] or "").replace("\n", " ")
                w1.writerow([eid, e["section"], e["no"], e["title"], e["page_from"], e["page_to"], e["printed_page"], prov,
                             e["explanation"], e["note"], f"{doc['url']}#page={e['page_from']}"])
                for ti, t in enumerate(e["tables"], 1):
                    for f in t["fields"]:
                        w2.writerow([eid, ti, t["role"], t["caption"], 0, f["label"], cell(f["value"]) + (f["unit"] or "")])
                    for ri, r in enumerate(t["rows"], 1):
                        for c, v in zip(t["columns"], r):
                            if v not in (None, ""):
                                # 横にまたがるセル（config の spans）: 行のどこかに row の文字があり、from の列のもの
                                to = next((sp["to"] for sp in e["spans"] if sp["from"] == c and sp["row"] in r
                                           and sp.get("role", t["role"]) == t["role"]), "")
                                w2.writerow([eid, ti, t["role"], t["caption"], ri, c, v, to])
                md += [f"## {eid}. {e['section'] or ''} No.{e['no'] or '-'} {e['title'] or ''}", "", "```", text, "```", ""]
        (out_dir / "examples.json").write_text(json.dumps(exs, ensure_ascii=False, indent=1), encoding="utf-8")
        (out_dir / "examples.md").write_text("\n".join(md), encoding="utf-8")
        print(f"{d['doc']}: 事例 {len(exs)} 件 → DB examples, {out_dir.relative_to(ROOT)}/examples.{{json,csv,md}}, example_cells.csv")
    con.commit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
