"""書き起こし結果の後処理（LLM を使わない、決定的な処理）。

1. 継続フラグ: モデルの自己申告を捨て、pagemeta（テキストレイヤ）の判定で上書きする
   （モデルの値は model_continued_from_prev_page / model_continues_to_next_page に残す）
2. 必須（列別）: 空欄の列を省いた行を、表の列見出しを基準に全列そろえる
3. 備考の「※n」を注記本文にひも付ける（同ページの footnotes → 無ければ次ページのテキストレイヤ）
4. ページをまたぐ表を結合し、論理的な表（logical_tables）を作る

usage: uv run python src/postprocess.py [--run anthropic-png]
出力: out/{run}-post/{model}/{doc_id}_p{page}.json（validate / report がそのまま読める形）
      out/{run}-post/{model}/logical_tables.json
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import shutil
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

import pymupdf
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pagemeta import doc_profile  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MARK = re.compile(r"※\s*([0-9A-Za-z]+)")


def nfkc(s) -> str:
    return unicodedata.normalize("NFKC", str(s or ""))


def col_key(c) -> str:
    c = nfkc(c)
    m = re.search(r"(?<!\d)\d{4}(?!\d)", c)
    return m.group(0) if m else re.sub(r"\s+", "", c.split(">")[-1])


def fill_required_by(table: dict) -> int:
    """列数の足りない行を、最も列数の多い行（＝列見出し）に合わせて補う。補った行数を返す。"""
    items = table.get("items") or []
    widths = [len(it.get("required_by") or []) for it in items]
    if not widths or max(widths) == 0 or min(widths) == max(widths):
        return 0
    ref = next(it["required_by"] for it in items if len(it.get("required_by") or []) == max(widths))
    ref_cols = [r["column"] for r in ref]
    fixed = 0
    for it in items:
        rb = it.get("required_by") or []
        if len(rb) == len(ref_cols) or not rb and it.get("required") is not None:
            continue
        by_key = {col_key(r["column"]): r.get("value") for r in rb}
        unknown = [k for k in by_key if k not in {col_key(c) for c in ref_cols}]
        if unknown:  # 対応づけられない列名がある行は触らない
            continue
        it["required_by"] = [{"column": c, "value": by_key.get(col_key(c))} for c in ref_cols]
        it.setdefault("_post", []).append("required_by を列見出しに合わせて補完")
        fixed += 1
    return fixed


def footnotes_from_text(page: pymupdf.Page) -> dict[str, str]:
    """テキストレイヤから「※n 本文」を拾う（次ページへ続いた注記用）。"""
    out: dict[str, str] = {}
    cur = None
    for ln in page.get_text().splitlines():
        s = nfkc(ln).strip()
        m = re.match(r"^※\s*([0-9A-Za-z]+)\s*(.*)$", s)
        if m:
            cur = m.group(1).upper()
            out[cur] = m.group(2)
        elif cur and s and not re.match(r"^[-\s]*\d", s):
            out[cur] += s
    return out


def link_footnotes(res: dict, next_page_notes: dict[str, str]) -> tuple[int, int]:
    notes = {}
    for fn in res.get("footnotes") or []:
        m = MARK.search(nfkc(fn.get("mark")))
        if m:
            notes[m.group(1).upper()] = (fn.get("text"), "page")
    resolved = unresolved = 0
    for t in res.get("tables") or []:
        for it in t.get("items") or []:
            refs = []
            for m in MARK.finditer(nfkc(it.get("note"))):
                k = m.group(1).upper()
                if k in notes:
                    refs.append({"mark": f"※{k}", "text": notes[k][0], "source": notes[k][1]})
                    resolved += 1
                elif k in next_page_notes:
                    refs.append({"mark": f"※{k}", "text": next_page_notes[k], "source": "next_page_textlayer"})
                    resolved += 1
                else:
                    refs.append({"mark": f"※{k}", "text": None, "source": None})
                    unresolved += 1
            if refs:
                it["note_refs"] = refs
    return resolved, unresolved


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="anthropic-png")
    args = ap.parse_args()
    src_dir = ROOT / "out" / args.run
    dst_dir = ROOT / "out" / f"{args.run}-post"
    if dst_dir.exists():
        shutil.rmtree(dst_dir)
    manifest = {e["id"]: e for e in yaml.safe_load((ROOT / "sources" / "manifest.yaml").read_text(encoding="utf-8"))}
    profiles: dict[str, list[dict]] = {}
    pdfs: dict[str, pymupdf.Document] = {}

    stats = defaultdict(lambda: defaultdict(int))
    for mdir in sorted(p for p in src_dir.iterdir() if p.is_dir()):
        model = mdir.name
        pages_by_doc: dict[str, list[tuple[int, dict]]] = defaultdict(list)
        for f in sorted(mdir.glob("*.json")):
            data = json.loads(f.read_text(encoding="utf-8"))
            res = data.get("result")
            if res is None:
                continue
            doc, page = data["meta"]["doc_id"], data["meta"]["page"]
            e = manifest[doc]
            pdf_path = ROOT / "sources" / "raw" / e["domain"] / f"{doc}.pdf"
            if doc not in profiles:
                profiles[doc] = doc_profile(pdf_path)
                pdfs[doc] = pymupdf.open(pdf_path)
            prof = profiles[doc][page - 1]
            res = copy.deepcopy(res)
            tabs = res.get("tables") or []
            # 1. 継続フラグ
            for i, t in enumerate(tabs):
                t["model_continued_from_prev_page"] = t.get("continued_from_prev_page")
                t["model_continues_to_next_page"] = t.get("continues_to_next_page")
                t["continued_from_prev_page"] = prof["continued_from_prev"] if i == 0 else False
                t["continues_to_next_page"] = prof["continues_to_next"] if i == len(tabs) - 1 else False
            # 2. 必須（列別）
            for t in tabs:
                stats[model]["required_by_rows_filled"] += fill_required_by(t)
            # 3. 注記
            nxt = next((p for p in profiles[doc][page:] if not p["blank"]), None)
            next_notes = footnotes_from_text(pdfs[doc][nxt["page"] - 1]) if nxt else {}
            r, u = link_footnotes(res, next_notes)
            stats[model]["note_marks_resolved"] += r
            stats[model]["note_marks_unresolved"] += u
            out = dst_dir / model / f.name
            out.parent.mkdir(parents=True, exist_ok=True)
            data["result"] = res
            data["meta"]["postprocessed"] = True
            out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            pages_by_doc[doc].append((page, res))

        # 4. ページをまたぐ表の結合
        logical = []
        for doc, pages in pages_by_doc.items():
            pages.sort(key=lambda x: x[0])
            cur = None
            prev_page = None
            for page, res in pages:
                for i, t in enumerate(res.get("tables") or []):
                    joinable = (i == 0 and t["continued_from_prev_page"] and cur is not None
                                and prev_page is not None
                                and all(p["blank"] for p in profiles[doc][prev_page:page - 1]))
                    if joinable:
                        cur["pages"].append(page)
                        cur["items"].extend(t.get("items") or [])
                        stats[model]["tables_joined"] += 1
                    else:
                        if cur:
                            logical.append(cur)
                        cur = {"doc_id": doc, "pages": [page], "table_kind": t.get("table_kind"),
                               "title": t.get("title"), "record": t.get("record"),
                               "columns": t.get("columns"), "items": list(t.get("items") or []),
                               "starts_mid_table": bool(t["continued_from_prev_page"])}
                prev_page = page
            if cur:
                logical.append(cur)
        for lt in logical:
            nos = [it.get("no") for it in lt["items"] if it.get("no") is not None]
            lt["no_range"] = [min(nos), max(nos)] if nos else None
            lt["no_gaps"] = [b for a, b in zip(nos, nos[1:]) if b not in (a, a + 1)]
        (dst_dir / model / "logical_tables.json").write_text(json.dumps(logical, ensure_ascii=False, indent=1), encoding="utf-8")
        stats[model]["logical_tables"] = len(logical)

    if (src_dir / "calls.jsonl").exists():  # コスト集計（report.py）用にそのまま引き継ぐ
        shutil.copy(src_dir / "calls.jsonl", dst_dir / "calls.jsonl")
    for m, s in stats.items():
        print(m, dict(s))
    print(f"→ {dst_dir.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
