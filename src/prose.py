"""表以外の文章（説明・ファイル構成・留意事項など）を PDF のテキストレイヤから取り出し、検索用の塊に分ける（API は使わない）。

表のページは、表より前（見出し・説明文）だけを使う。表の中身は書き起こし（items）の方にあるので重ねない。
図の中の文字は、テキストレイヤにあれば拾えるが、配置の意味（矢印・枠）は失われる。
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pymupdf

from exchange_ids import HEAD
from pagemeta import doc_profile

CJK = re.compile(r"[　-ヿ㐀-鿿＀-￯]")
PAGE_NO = re.compile(r"^[-－‐\s]*[0-9０-９]+(?:\s*[-－‐]\s*[0-9０-９]+)?[-－‐\s]*$")


def nk(s) -> str:
    return unicodedata.normalize("NFKC", str(s or ""))


def clean_lines(lines: list[str]) -> str:
    """改行で切れた日本語をつなぐ。縦書き（1〜2文字の行が続く）はひと続きにする。"""
    out = ""
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        if out and not (CJK.search(out[-1]) and CJK.search(ln[0])):
            out += " "
        out += ln
    return re.sub(r"\s{2,}", " ", out)


def page_text(page: pymupdf.Page, has_table: bool) -> tuple[str, str | None]:
    """(本文, 印刷ページ番号)。表のページは最初の「項番」より前だけ。"""
    lines = [ln for ln in page.get_text().splitlines()]
    printed = None
    for ln in lines[:3] + lines[-3:]:
        if PAGE_NO.match(nk(ln).strip()) and nk(ln).strip():
            printed = nk(ln).strip(" -－‐")
            break
    lines = [ln for ln in lines if not PAGE_NO.match(nk(ln).strip())]
    if has_table:
        cut = next((i for i, ln in enumerate(lines) if nk(ln).strip() in ("項番", "項", "No", "NO")), len(lines))
        lines = lines[:cut]
    return clean_lines(lines), printed


def split(text: str, size: int = 700) -> list[str]:
    """文（。）の区切りで size 文字程度に分ける。前の塊の最後の文を次の塊の頭に重ねる。"""
    sents = [s for s in re.split(r"(?<=。)", text) if s.strip()]
    chunks, cur = [], []
    for s in sents:
        while len(s) > size:  # 句点の無い長い文（図・表の残り）は機械的に切る
            chunks.append("".join(cur) + s[:size])
            cur, s = [], s[size:]
        if cur and len("".join(cur)) + len(s) > size:
            chunks.append("".join(cur))
            cur = cur[-1:]
        cur.append(s)
    if cur and "".join(cur).strip():
        chunks.append("".join(cur))
    # 目次（「…………」の続く行）は検索の邪魔になるので外す
    return [c.strip() for c in chunks if len(c.strip()) >= 40 and len(re.findall(r"[.．…・]{5,}", c)) < 3]


def doc_prose(pdf: Path) -> list[dict]:
    """[{page, printed_page, section, text}]（節は直前の見出しを引き継ぐ）"""
    prof = doc_profile(pdf)
    out = []
    section = None
    with pymupdf.open(pdf) as d:
        for i, pg in enumerate(d):
            p = prof[i]
            for ln in pg.get_text().splitlines():
                m = HEAD.match(nk(ln).strip())
                if m and len(m.group(2)) <= 60:
                    section = f"{m.group(1)} {m.group(2).strip()}"
            if p["blank"]:
                continue
            text, printed = page_text(pg, p["has_table"])
            for c in split(text):
                out.append({"page": i + 1, "printed_page": printed, "section": section, "text": c})
    return out
