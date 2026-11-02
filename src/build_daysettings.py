"""書き起こした「設定方法の表」（日数情報レコードの設定方法など）を採用して、DB の day_settings テーブルと CSV にする。

usage: uv run python src/build_daysettings.py [--config config/daysettings.yaml] [--db db/interface_spec.sqlite]
  前提: transcribe_examples.py --kind daysettings で out/daysettings/{doc}/{haiku,sonnet}/p*.json を作ってある。
        build_db.py の後に実行する（build_db.py は DB を作り直すので、そのたびにこれもやり直す）。この後に build_index.py。
  1件 = 「事務処理要領」のセルを共有するサービスのまとまり。「（N）と同様」は引いた先の設定例を本文に付け、
  サービス名などの ※N には、その頁（無ければ近くの頁）の注記を付ける。
出力:
  DB の day_settings テーブル（1件1行）と day_setting_pages テーブル（取り込んだ頁。build_index.py はこの頁の本文を使わない）
  out/daysettings/{doc}/day_settings.csv（サービス1つ1行）・day_settings.md（人が読む用）
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from transcribe_examples import parse_pages  # noqa: E402

REF = re.compile(r"[（(]\s*(\d+)\s*[)）]\s*と同様")
MARK = re.compile(r"※\s*(\d+)")


def nfkc(s: str | None) -> str:
    return unicodedata.normalize("NFKC", s or "")


def mark_no(mark: str) -> str:
    """'※１' → '1'"""
    m = MARK.search(nfkc(mark))
    return m.group(1) if m else nfkc(mark).strip()


def load_part(doc: str, pages: list[int], base: str, use: dict, notes: dict, label: str | None) -> list[dict]:
    res = {p: json.loads((ROOT / "out" / "daysettings" / doc / use.get(str(p), base) / f"p{p}.json")
                         .read_text(encoding="utf-8"))["result"] for p in pages}
    # 注記: 頁の注記 → 無ければ次の頁が注記だけの頁ならそれ → 無ければ前の頁
    foot: dict[int, tuple[int, list]] = {}
    for i, p in enumerate(pages):
        r = res[p]
        if r["footnotes"]:
            foot[p] = (p, r["footnotes"])
        elif i + 1 < len(pages) and not res[pages[i + 1]]["sections"] and res[pages[i + 1]]["footnotes"]:
            foot[p] = (pages[i + 1], res[pages[i + 1]]["footnotes"])
        elif i > 0 and foot.get(pages[i - 1]):
            foot[p] = foot[pages[i - 1]]
    out: list[dict] = []
    heading = None
    for p in pages:
        r = res[p]
        heading = r["heading"] or heading
        gi = 0
        for s in r["sections"]:
            for g in s["groups"]:
                services = [{"name": re.sub(r"\s*\n\s*", "", x["name"]), "code": x["code"]} for x in g["services"]]
                used = {m for x in [*(x["name"] for x in services), g["procedure"], g["example_text"]] for m in MARK.findall(nfkc(x))}
                fp, fn = foot.get(p, (None, []))
                out.append({"doc_id": doc, "page": p, "printed_page": r["printed_page"], "part": label, "heading": heading,
                            "section": s["title"], "services": services, "procedure": g["procedure"],
                            "example_text": g["example_text"], "example_tables": g["example_tables"],
                            "footnotes": [f for f in fn if mark_no(f["mark"]) in used],
                            "footnote_page": fp, "note": notes.get(f"{p}#{gi}"), "model": use.get(str(p), base), "ref": None})
                gi += 1
    # 「（N）と同様」: 同じ part の中で（N）から始まるデータ設定例。（N）の番号は帯をまたいで重なる
    # （③利用日数の (9)(10) と ④入院日数の (9)・⑤外泊日数の (10)）ので、同じ帯 → 前の帯の近いもの の順に探す
    for i, e in enumerate(out):
        m = REF.search(nfkc(e["example_text"]))
        if m:
            cand = [x for x in out if x is not e and re.match(rf"\s*\(\s*{m.group(1)}\s*\)", nfkc(x["example_text"]))]
            src = next((x for x in cand if nfkc(x["section"]) == nfkc(e["section"])), None)                 or next((x for x in reversed(out[:i]) if x in cand), None)
            if src is None:
                raise SystemExit(f"p{e['page']} {e['section']}: 「({m.group(1)})と同様」の引き先が見つからない")
            e["ref"] = {"no": m.group(1), "page": src["page"], "section": src["section"],
                        "example_text": src["example_text"], "example_tables": src["example_tables"]}
            # 引いた先の文の ※N にも、引いた先の頁の注記を付ける
            used = set(MARK.findall(nfkc(src["example_text"])))
            fn = foot.get(src["page"], (None, []))[1]
            e["footnotes"] += [f for f in fn if mark_no(f["mark"]) in used and f not in e["footnotes"]]
    return out


def table_lines(tables: list[dict]) -> list[str]:
    lines = []
    for t in tables:
        lines.append(f"  表{('「' + t['caption'] + '」') if t['caption'] else ''}: 列 " + " | ".join(t["columns"]))
        lines += ["    " + " | ".join("" if v is None else v for v in row) for row in t["rows"]]
    return lines


def render_text(e: dict, head: str) -> str:
    pp = f"、印刷 {e['printed_page']}" if e["printed_page"] else ""
    title = " ".join(x for x in (e["part"], nfkc(e["heading"]).strip() if e["heading"] else None) if x)
    lines = [head, f"設定方法: {title} {e['section']}（PDF p{e['page']}{pp}）",
             "対象のサービス種類: " + "、".join(f"{x['name']}（{x['code']}）" if x["code"] else x["name"] for x in e["services"]),
             "事務処理要領: " + (e["procedure"] or "")]
    lines.append("データ設定例: " + (e["example_text"] or ""))
    lines += table_lines(e["example_tables"])
    if e["ref"]:
        lines.append(f"「（{e['ref']['no']}）と同様」の（{e['ref']['no']}）（{e['ref']['section']}、PDF p{e['ref']['page']}）: "
                     f"{e['ref']['example_text']}")
        lines += table_lines(e["ref"]["example_tables"])
    if e["footnotes"]:
        lines.append("注記: " + " ".join(f"{f['mark']} {f['text']}" for f in e["footnotes"]))
    if e["note"]:
        lines.append("書き起こしの注記: " + e["note"])
    return "\n".join(lines)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/daysettings.yaml")
    ap.add_argument("--db", default="db/interface_spec.sqlite")
    args = ap.parse_args()
    cfg = yaml.safe_load((ROOT / args.config).read_text(encoding="utf-8"))
    con = sqlite3.connect(ROOT / args.db)
    con.row_factory = sqlite3.Row
    con.executescript("""
DROP TABLE IF EXISTS day_settings;
CREATE TABLE day_settings (setting_id INTEGER PRIMARY KEY, doc_id TEXT NOT NULL, page INTEGER, printed_page TEXT, part TEXT,
                           heading TEXT, section TEXT, services TEXT, procedure TEXT, example_text TEXT, example_tables TEXT,
                           ref TEXT, footnotes TEXT, note TEXT, model TEXT, text TEXT NOT NULL);
DROP TABLE IF EXISTS day_setting_pages;
CREATE TABLE day_setting_pages (doc_id TEXT NOT NULL, page INTEGER NOT NULL, PRIMARY KEY (doc_id, page));
""")
    sid = 0
    for d in cfg["docs"]:
        doc = con.execute("SELECT * FROM documents WHERE doc_id = ?", (d["doc"],)).fetchone()
        head = f"{'障害福祉' if doc['domain'] == 'shogai' else '介護保険'} インタフェース仕様書 {doc['volume']} {doc['edition']}"
        rows: list[dict] = []
        for part in d["parts"]:
            pages = parse_pages(str(part["pages"]))
            rows += load_part(d["doc"], pages, d["base"], {str(k): v for k, v in (d.get("use") or {}).items()},
                              d.get("notes") or {}, part.get("label"))
            con.executemany("INSERT INTO day_setting_pages VALUES (?, ?)", [(d["doc"], p) for p in pages])
        out_dir = ROOT / "out" / "daysettings" / d["doc"]
        md = [f"# 設定方法の表: {head}", "", f"{len(rows)} 件。`src/build_daysettings.py` が作る（手で直さない）。", ""]
        with (out_dir / "day_settings.csv").open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["setting_id", "part", "section", "pdf_page", "printed_page", "service_name", "service_code",
                        "procedure", "example_text", "same_as", "note", "url"])
            for e in rows:
                sid += 1
                text = render_text(e, head)
                con.execute("INSERT INTO day_settings VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            (sid, e["doc_id"], e["page"], e["printed_page"], e["part"], e["heading"], e["section"],
                             json.dumps(e["services"], ensure_ascii=False), e["procedure"], e["example_text"],
                             json.dumps(e["example_tables"], ensure_ascii=False), json.dumps(e["ref"], ensure_ascii=False),
                             json.dumps(e["footnotes"], ensure_ascii=False), e["note"], e["model"], text))
                for x in e["services"]:
                    w.writerow([sid, e["part"], e["section"], e["page"], e["printed_page"], x["name"], x["code"], e["procedure"],
                                e["example_text"], f"（{e['ref']['no']}）p{e['ref']['page']}" if e["ref"] else "", e["note"],
                                f"{doc['url']}#page={e['page']}"])
                md += [f"## {sid}. {e['part']} {e['section']} p{e['page']}", "", "```", text, "```", ""]
        (out_dir / "day_settings.md").write_text("\n".join(md), encoding="utf-8")
        print(f"{d['doc']}: {len(rows)} 件 → DB day_settings, {out_dir.relative_to(ROOT)}/day_settings.{{csv,md}}")
    con.commit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
