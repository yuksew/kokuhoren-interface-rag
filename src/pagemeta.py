"""PDF のテキストレイヤだけで分かるページ情報（LLM を使わない）。

- blank: 「このページは空白です」等のページ
- has_table: 表のあるページか（「項番」の見出し、または様式種別番号の並び）
- starts_with_table: ページ先頭（ページ番号を除く）が表の見出し行から始まる
  ＝ 表見出し（・…レコード、（n）…）が無く、前ページの表の続き
- continued_from_prev / continues_to_next: 上を前後の非空白ページと突き合わせて決める

usage: uv run python src/pagemeta.py [doc_id ...]   → out/pagemeta/{doc_id}.json と集計を出す
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

import pymupdf
import yaml

ROOT = Path(__file__).resolve().parent.parent

# ページ番号行: 「- ３８ -」「- ３１－１ -」「１６」「62−7」など
PAGE_NO = re.compile(r"^[-－―\s]*[0-9０-９]+([－\-−―][0-9０-９]+)*[-－―\s]*$")
# 表の見出し行の先頭語
HEADER_START = re.compile(r"^(項\s*番|項$|様式種別番号|[0-9]{4}$)")
BLANK = re.compile(r"このページは空白です")


def nfkc(s: str) -> str:
    return unicodedata.normalize("NFKC", s)


def lines_of(page: pymupdf.Page) -> list[str]:
    return [ln.strip() for ln in page.get_text().splitlines() if ln.strip()]


def profile(page: pymupdf.Page) -> dict:
    L = lines_of(page)
    body = [ln for ln in L if not PAGE_NO.match(nfkc(ln))]
    text = nfkc("".join(L))
    blank = bool(BLANK.search(text)) and len(body) <= 8
    first = nfkc(body[0]) if body else ""
    # 「項番」が見出しセルとして単独の行にある（本文中の「① 項番」などは数えない）、または様式種別番号が並ぶ
    norm_lines = [nfkc(ln).strip() for ln in body]
    header_cell = any(re.fullmatch(r"項\s*番(\s*(識別|項目名|コード名称))?", ln) for ln in norm_lines) or any(
        a == "項" and b == "番" for a, b in zip(norm_lines, norm_lines[1:]))  # 縦書き・2行に割れた「項／番」
    has_table = (not blank) and (header_cell or len(re.findall(r"(?<!\d)\d{4}(?!\d)", " ".join(body[:30]))) >= 8)
    # 「Ｎｏ」見出しの表は記載例（実績記録票の時間帯図・紙様式との対応など）が多い。仕様の表とは分けて記録する
    has_example_table = (not blank) and not has_table and any(re.fullmatch(r"No\.?", ln) for ln in norm_lines)
    return {
        "blank": blank,
        "has_table": has_table,
        "has_example_table": has_example_table,
        "starts_with_table": (not blank) and bool(HEADER_START.match(first)),
        "first_line": body[0] if body else None,
    }


def doc_profile(pdf: Path) -> list[dict]:
    with pymupdf.open(pdf) as d:
        profs = [{"page": i + 1, **profile(p)} for i, p in enumerate(d)]
    # 前後の非空白ページと突き合わせる
    nonblank = [p for p in profs if not p["blank"]]
    for prev, cur in zip(nonblank, nonblank[1:]):
        cont = cur["starts_with_table"] and prev["has_table"]
        cur["continued_from_prev"] = cont
        prev["continues_to_next"] = cont
    for p in profs:
        p.setdefault("continued_from_prev", False)
        p.setdefault("continues_to_next", False)
    return profs


def main() -> int:
    manifest = yaml.safe_load((ROOT / "sources" / "manifest.yaml").read_text(encoding="utf-8"))
    ids = sys.argv[1:] or [e["id"] for e in manifest if e["kind"] == "spec"]
    by_id = {e["id"]: e for e in manifest}
    out_dir = ROOT / "out" / "pagemeta"
    out_dir.mkdir(parents=True, exist_ok=True)
    total = tables = 0
    for i in ids:
        e = by_id[i]
        profs = doc_profile(ROOT / "sources" / "raw" / e["domain"] / f"{i}.pdf")
        (out_dir / f"{i}.json").write_text(json.dumps(profs, ensure_ascii=False, indent=1), encoding="utf-8")
        n_tab = sum(p["has_table"] for p in profs)
        total += len(profs)
        tables += n_tab
        print(f"{i:32s} pages={len(profs):4d} table_pages={n_tab:4d} blank={sum(p['blank'] for p in profs):3d}")
    print(f"合計 pages={total} table_pages={tables}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
