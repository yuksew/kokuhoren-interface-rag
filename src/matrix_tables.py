"""表の判定から漏れていた表のうち、画像からの書き起こしより PDF のテキストレイヤと罫線から組み立てる方が確かなものを、確定版にする。

usage: uv run python src/matrix_tables.py [--check]
  この後に build_db.py（既定の run に matrix-textlayer が入っている）。API は使わない。
  --check: 書き出さずに、組み立てた行を出す
対象:
  BLOCKS: 障害 都道府県編の、事業所異動連絡票情報（サービス情報）・障害児施設異動連絡票情報（サービス情報）の記載要領の後にある
    「サービス種類ごとの設定項目」の表（行: サービス種類、列: 項目、セル: ○）。異動年月日の期間ごとに同じ形の表があり、
    今の期間（令和8年6月以降）だけを入れる（障害 p54〜59、障害児 p288〜290。古い期間は p60〜132・p291〜314）。
    1つの表が横に数頁続く（どの頁も行は同じサービス種類で、左の列も同じ。右の項目の列が頁ごとに違う）ので、
    サービス種類で頁をつないで 1 つの表にする。
  PAIR_BLOCKS: 介護 保険者編 p210〜212「データの充当を行なわない項目とその条件」（項目｜引き継がない条件 の 2 列。右の列は行をまたいで結合）
組み立て方:
  - 頁が 90 度回してあるときは、文字と罫線の座標を rotation_matrix で見た目の向きに直す
  - 列: 本体を縦に通る罫線（細切れの線は長さを足す）。行: 左端の列を横切る罫線（二重線はまとめる）
  - 見出し（縦書き）: 列の中の文字を、PDF の文字の順のまま（縦の列ごとに上から、右の列から）つなぐ
  - 斜線のセル（対象外）は文字が無いので空のまま
  - 結合したセル: 右の列の罫線で区切った範囲を、範囲に入る左の行すべてに付ける
出力: out/matrix-textlayer-reviewed/{doc}_p{n}.json（頁ごと。表は最初の頁にだけ置く）と logical_tables.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from transcribe import load_manifest, pdf_path  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RUN = "matrix-textlayer"

BLOCKS = [
    {"doc": "shogai_todofuken_r0806", "pages": list(range(54, 60)),
     "record": "事業所異動連絡票情報（サービス情報）"},
    {"doc": "shogai_todofuken_r0806", "pages": list(range(288, 291)),
     "record": "障害児施設異動連絡票情報（サービス情報）"},
]
LEFT_NAMES = {"サービス種類", "施設等の区分", "人員配置区分", "障害児施設区分"}   # どの頁にもある左の列（障害児は人員配置区分が無い）


def nk(s: str) -> str:
    return unicodedata.normalize("NFKC", s).replace("〇", "○")


def grid(page: pymupdf.Page):
    M = page.rotation_matrix
    V, H = [], []
    for g in page.get_drawings():
        for it in g["items"]:
            if it[0] == "l":
                a, b = it[1] * M, it[2] * M
                if abs(a.x - b.x) < 0.5:
                    V.append((a.x, min(a.y, b.y), max(a.y, b.y)))
                elif abs(a.y - b.y) < 0.5:
                    H.append((a.y, min(a.x, b.x), max(a.x, b.x)))
            elif it[0] == "re":
                r = it[1] * M
                if r.width < 1.5 and r.height > 3:
                    V.append((r.x0 + r.width / 2, r.y0, r.y1))
                elif r.height < 1.5 and r.width > 3:
                    H.append((r.y0 + r.height / 2, r.x0, r.x1))
                elif r.width >= 1.5 and r.height >= 1.5:
                    V += [(r.x0, r.y0, r.y1), (r.x1, r.y0, r.y1)]
                    H += [(r.y0, r.x0, r.x1), (r.y1, r.x0, r.x1)]
    return V, H


def merge(vals: list[float], gap: float = 2.0) -> list[float]:
    out: list[float] = []
    for v in sorted(vals):
        if not out or v - out[-1] > gap:
            out.append(v)
    return out


def page_lines(page: pymupdf.Page) -> list[tuple[float, float, str]]:
    """PDF の行ごと (x の中心, y の中心, 文字列)。PDF の順のまま"""
    M = page.rotation_matrix
    out = []
    for b in page.get_text("rawdict")["blocks"]:
        for ln in b.get("lines", []):
            s = "".join(c["c"] for sp in ln["spans"] for c in sp["chars"])
            if s.strip():
                r = pymupdf.Rect(ln["bbox"]) * M
                out.append(((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2, s))
    return out


def text_in(lines, x0, x1, y0, y1, sep: str = "") -> str | None:
    s = sep.join(t for x, y, t in lines if x0 <= x < x1 and y0 <= y < y1)
    s = re.sub(r"\s+", " ", nk(s)).strip()
    return s or None


def extract_page(page: pymupdf.Page) -> dict:
    V, H = grid(page)
    lines = page_lines(page)
    height = max(b for _, _, b in V) - min(a for _, a, _ in V)
    # 本体を縦に通る罫線。線は細切れのことがあるので、同じ x（1pt 以内）の長さを足して見る
    cover: dict[float, float] = {}
    for x, a, b in sorted(V):
        k = next((k for k in cover if abs(k - x) <= 1), x)
        cover[k] = cover.get(k, 0) + (b - a)
    xs = merge([x for x, n in cover.items() if n > height * 0.6])
    left_x0, left_x1 = xs[0], xs[1]
    xc = (left_x0 + left_x1) / 2
    ys = merge([y for y, a, b in H if a <= xc <= b])   # 左端の列の中央を横切る罫線
    # 見出しの下端: 最初のサービス（「11:」のような行）の上の罫線
    first = min(y for x, y, t in lines if left_x0 <= x < left_x1 and re.match(r"\s*\d+\s*[:：]", nk(t)))
    hb = max(y for y in ys if y < first)
    period = next((m.group(1) for x, y, t in lines if (m := re.search(r"【\s*(異動年月日の年月が.+?の場合)\s*】", nk(t)))), None)
    head_top = min(y for y in ys)
    cols = [text_in(lines, a, b, head_top, hb) or "" for a, b in zip(xs, xs[1:])]
    # 期間の帯（【…】）は左の列の見出しの上にかかるので、左の列の見出しからは除く
    cols = [re.sub(r"【.*?】", "", c).strip() for c in cols]
    rows = []
    for y0, y1 in zip([y for y in ys if y >= hb], [y for y in ys if y > hb]):
        cells = [text_in(lines, a, b, y0, y1, sep=" ") for a, b in zip(xs, xs[1:])]
        if cells[0]:
            rows.append(cells)
    pp = next((m.group(1) for x, y, t in lines
               if y > ys[-1] and (m := re.fullmatch(r"\s*[-－−]\s*(\d+(?:\s*[-－−]\s*\d+)?)\s*[-－−]\s*", nk(t)))), None)
    return {"period": period, "columns": cols, "rows": rows,
            "printed_page": pp and re.sub(r"[－−]", "-", re.sub(r"\s", "", pp))}


def service(s: str) -> tuple[str, str]:
    """'11:居宅介護' → ('11', '居宅介護')。コードが名前の後に来るセルもある（'就労移行支援 (養成施設) 44:'）"""
    m = re.search(r"(\d+)\s*[:：]", s)
    if not m:
        return s, s
    return m.group(1), (s[:m.start()] + s[m.end():]).replace(" ", "")


def service_key(s: str) -> str:
    return service(s)[0]


def build_block(pdf, blk: dict) -> dict:
    pages = [extract_page(pdf[p - 1]) for p in blk["pages"]]
    LEFT = next(i for i, c in enumerate(pages[0]["columns"]) if c not in LEFT_NAMES)
    left = pages[0]["columns"][:LEFT]
    keys = [service_key(r[0]) for r in pages[0]["rows"]]
    for p, pg in zip(blk["pages"], pages):
        if pg["columns"][:LEFT] != left or [service_key(r[0]) for r in pg["rows"]] != keys:
            raise SystemExit(f"p{p}: 左の列か行が最初の頁と違う: {pg['columns'][:LEFT]} {len(pg['rows'])} 行")
        if pg["period"] != pages[0]["period"]:
            raise SystemExit(f"p{p}: 期間が違う: {pg['period']}")
    item_cols = [(p, c) for p, pg in zip(blk["pages"], pages) for c in pg["columns"][LEFT:]]
    items = []
    for i, k in enumerate(keys):
        r0 = pages[0]["rows"][i]
        name = service(r0[0])[1]
        marked, other = [], []
        for pg in pages:
            for c, v in zip(pg["columns"][LEFT:], pg["rows"][i][LEFT:]):
                if v == "○":
                    marked.append(c)
                elif v:
                    other.append({"column": c, "value": v})
        items.append({
            "no": None, "no_raw": k, "name_path": [name], "type": None, "length": None, "length_raw": None,
            "content": "○の付いた項目: " + ("、".join(marked) if marked else "なし"),
            "required": None, "required_by": [], "note": None,
            "cells": [{"column": c, "value": v} for c, v in zip(left[1:], r0[1:LEFT]) if v] + other,
            "page": blk["pages"][0], "_marked": len(marked)})
    return {"period": pages[0]["period"], "left": left, "item_cols": item_cols, "items": items,
            "shape": [(p, len(pg["columns"]), len(pg["rows"])) for p, pg in zip(blk["pages"], pages)],
            "printed": {p: pg["printed_page"] for p, pg in zip(blk["pages"], pages)}}


PAIR_BLOCKS = [
    # 保険者 → 国保連の台帳交換情報で、直前の履歴から未設定の項目を充当するとき、充当しない項目と条件（右の列は行をまたいで結合）
    {"doc": "kaigo_hokensha_r0806_1", "pages": [210, 211, 212], "title": "データの充当を行なわない項目とその条件",
     "section": "1.5.1 交換情報の作成方法", "columns": ["項目", "引き継がない条件"]},
]


ITEM_END = r"(年月日|番号|コード|の有無)$"   # 項目名の終わり。行がここで終わっていれば、右端近くまであっても次の行は別の項目


def cell_text(page: pymupdf.Page, x0, x1, y0, y1, names: bool = False) -> str | None:
    """セルの中の文字。行が右端まで届いていれば折り返しとみなしてつなぎ、届いていなければ「、」で区切る（項目名の並び）。
    「・」で始まる行は箇条書きの始まり"""
    rows = []
    for b in page.get_text("rawdict", clip=pymupdf.Rect(x0, y0, x1, y1))["blocks"]:
        for ln in b.get("lines", []):
            cs = [c for sp in ln["spans"] for c in sp["chars"] if x0 <= (c["bbox"][0] + c["bbox"][2]) / 2 < x1
                  and y0 <= (c["bbox"][1] + c["bbox"][3]) / 2 < y1]
            t = "".join(c["c"] for c in cs)
            if t.strip():
                rows.append((cs[0]["bbox"][1], max(c["bbox"][2] for c in cs), t.strip()))
    rows.sort()
    out = ""
    for i, (y, right, t) in enumerate(rows):
        if i and t.startswith("・"):
            out += "\n"
        elif i and not out.endswith(("\n", "、")) and (rows[i - 1][1] < x1 - 14 or (names and re.search(ITEM_END, rows[i - 1][2]))):
            out += "、"
        out += t
    out = re.sub(r"[ \u3000]+", " ", nk(out)).strip()
    return out or None


def extract_pairs(page: pymupdf.Page, names: list[str]) -> list[tuple[str, str | None]]:
    V, H = grid(page)
    words = page.get_text("words")
    head = next(w for w in words if nk(w[4]) == nk(names[-1]))
    xs = merge([x for x, a, b in V if a <= head[1] <= b])
    xs = [xs[0], xs[-1]] if len(xs) == 2 else xs
    out = []
    cuts = {}
    for i, (a, b) in enumerate(zip(xs, xs[1:])):
        xc = (a + b) / 2
        # 列の幅いっぱいの線だけ（網掛け（黄色のマーカー）の長方形の辺は罫線ではない）
        ys = merge([y for y, h0, h1 in H if h0 <= a + 2 and h1 >= b - 2 and y > head[1]])
        cuts[i] = list(zip(ys, ys[1:]))
    for y0, y1 in cuts[0]:
        left = cell_text(page, xs[0], xs[1], y0, y1, names=True)
        ym = (y0 + y1) / 2
        r = next(((a, b) for a, b in cuts[1] if a <= ym < b), None)
        right = cell_text(page, xs[1], xs[2], *r) if r else None
        if left and nk(left) != nk(names[0]):
            out.append((left, right))
    return out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    man = load_manifest()
    out_dir = ROOT / "out" / f"{RUN}-reviewed"
    logical = []
    page_json: dict[tuple[str, int], dict] = {}
    for blk in BLOCKS:
        doc = blk["doc"]
        e = man[doc]
        pdf = pymupdf.open(pdf_path(e))
        b = build_block(pdf, blk)
        print(f"{doc} p{blk['pages'][0]}〜{blk['pages'][-1]} {blk['record']}（{b['period']}）: "
              f"{len(b['items'])} 行 × 項目 {len(b['item_cols'])} 列  頁ごと(頁, 列, 行) {b['shape']}")
        if args.check:
            print("  左の列:", b["left"])
            for it in b["items"]:
                print(f"  {it['no_raw']}:{it['name_path'][0]} ○{it['_marked']}  "
                      + " / ".join(f"{c['column']}={c['value']}" for c in it["cells"]))
            for p, c in b["item_cols"]:
                print(f"  列 p{p}: {c}")
            continue
        for it in b["items"]:
            it.pop("_marked")
        title = f"{blk['record']}のサービス種類ごとの設定項目（{b['period']}）"
        table = {"table_kind": "service_item_matrix", "title": title,
                 "record": {"exchange_id": "", "name": blk["record"], "parent": ""},
                 "columns": b["left"] + [c for _, c in b["item_cols"]],
                 "column_map": {"no": "", "name": b["left"][0], "type": "", "length": "", "content": "", "required": "", "note": ""},
                 "items": b["items"], "continued_from_prev_page": False, "continues_to_next_page": False,
                 "source_model": "textlayer"}
        for p in blk["pages"]:
            page_json[(doc, p)] = {"domain": e["domain"], "doc_id": doc, "page": p, "edition": e.get("edition"),
                                   "volume": e.get("volume"), "printed_page": b["printed"][p],
                                   "tables": [table] if p == blk["pages"][0] else [], "footnotes": [], "uncertain": [],
                                   "_fixes": [{"by": "textlayer", "note": f"src/matrix_tables.py が組み立てた（{title}、"
                                                                         f"p{blk['pages'][0]}〜{blk['pages'][-1]} を横につないだ）"}]}
        logical.append({"doc_id": doc, "pages": blk["pages"], "table_kind": table["table_kind"], "title": title,
                        "record": table["record"], "columns": table["columns"], "column_map": table["column_map"],
                        "items": b["items"], "starts_mid_table": False, "source_model": "textlayer"})
    for blk in PAIR_BLOCKS:
        doc = blk["doc"]
        e = man[doc]
        pdf = pymupdf.open(pdf_path(e))
        items = []
        for p in blk["pages"]:
            for left, right in extract_pairs(pdf[p - 1], blk["columns"]):
                items.append({"no": None, "no_raw": None, "name_path": [left], "type": None, "length": None,
                              "length_raw": None, "content": right, "required": None, "required_by": [], "note": None,
                              "cells": [], "page": p})
            pp = next((m.group(1) for w in pdf[p - 1].get_text("blocks")
                       if (m := re.fullmatch(r"\s*[-－−]\s*(\d+(?:\s*[-－−]\s*\d+)?)\s*[-－−]\s*", nk(w[4])))), None)
            page_json[(doc, p)] = {"domain": e["domain"], "doc_id": doc, "page": p, "edition": e.get("edition"),
                                   "volume": e.get("volume"),
                                   "printed_page": pp and re.sub(r"[－−]", "-", re.sub(r"\s", "", pp)),
                                   "tables": [], "footnotes": [], "uncertain": [],
                                   "_fixes": [{"by": "textlayer", "note": f"src/matrix_tables.py が組み立てた（{blk['title']}）"}]}
        print(f"{doc} p{blk['pages'][0]}〜{blk['pages'][-1]} {blk['title']}: {len(items)} 行")
        if args.check:
            for it in items:
                print(f"  [p{it['page']}] {it['name_path'][0]}\n      → {it['content']}")
            continue
        cm = {"no": "", "name": blk["columns"][0], "type": "", "length": "", "content": blk["columns"][1], "required": "", "note": ""}
        page_json[(doc, blk["pages"][0])]["tables"] = [{
            "table_kind": "other", "title": blk["title"], "record": {"exchange_id": "", "name": "", "parent": ""},
            "columns": blk["columns"], "column_map": cm, "items": items, "continued_from_prev_page": False,
            "continues_to_next_page": False, "source_model": "textlayer"}]
        logical.append({"doc_id": doc, "pages": blk["pages"], "table_kind": "other", "title": blk["title"],
                        "record": {"exchange_id": "", "name": "", "parent": ""}, "columns": blk["columns"], "column_map": cm,
                        "items": items, "starts_mid_table": False, "source_model": "textlayer"})
    if args.check:
        return 0
    out_dir.mkdir(parents=True, exist_ok=True)
    for (doc, p), j in page_json.items():
        (out_dir / f"{doc}_p{p}.json").write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
    (out_dir / "logical_tables.json").write_text(json.dumps(logical, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"→ {out_dir.relative_to(ROOT)}/（頁 {len(page_json)}、表 {len(logical)}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
