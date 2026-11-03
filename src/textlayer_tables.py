"""画像からの書き起こしが難しい細かい表を、PDF のテキストレイヤ（文字の位置）と罫線から組み立てて、確定版の表を差し替える。

usage: uv run python src/textlayer_tables.py --run prod5-png-post [--check]
  前提: apply_review.py を実行済み（out/{run}-reviewed/ がある）。この後に build_db.py。
  --check: 差し替えずに、確定版（Haiku など）との違いだけを出す
対象（LAYOUTS）: 障害 共通編のインタフェース一覧（PDF p57〜63）。1頁 70〜90 行 × 18 列で文字が小さく、
  Sonnet は書き起こしを省き、Haiku は値の読み違いが頁に 3〜28 個あった。PDF は文字を持っているので、そちらを正とする。
組み立て方:
  - 列: 縦の罫線の位置（全頁で同じ）。罫線の無い小さな列（データ種別｜交換情報識別番号、対応業務の 7 列）は見出しの位置で分ける
  - 行: No の列の文字の位置（行の間の罫線は点線で拾えないので）。文字は1文字ずつ、中心の位置で行と列に振り分ける
  - 縦に結合したセル（左の4列: 仕様書・業務種別・業務内容・情報区分）: その列を横切る罫線で区切った範囲の文字を、
    範囲に入る行すべてに入れる（範囲に文字が無ければ上の行の値。頁をまたいでも）。データ種別は、空の行のうち上の行との境目に
    線が無いもの（頁の画像の明るさで見る）だけ上の値を入れる。それ以外の列は行ごと（空欄は空欄のまま）
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pagemeta import doc_profile  # noqa: E402
from postprocess import build_logical  # noqa: E402
from transcribe import load_manifest, pdf_path  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

SUPPORT = ["障害福祉サービス", "障害福祉サービス（基準該当）", "障害児支援", "障害児支援（基準該当）", "地域生活支援事業",
           "高額障害福祉サービス等給付費", "高額障害児給付費"]
LAYOUTS = {
    "shogai_kyotsu_r0710": {
        "pages": range(57, 64),
        "title": "インタフェース一覧",
        "table_kind": "interface_list",
        # (列名, 左端, 右端)。x は PDF の座標（pt）
        "columns": [("インタフェース仕様書", 30, 56), ("業務種別", 56, 93), ("業務内容", 93, 138), ("情報区分", 138, 206),
                    ("データ種別", 206, 220), ("交換情報識別番号", 220, 239), ("No", 239, 249), ("情報名", 249, 386),
                    ("ルート", 386, 402), ("周期", 402, 417), ("媒体区分", 417, 430)]
                   + [(f"対応業務 > {s}", 430 + i * (142 / 7), 430 + (i + 1) * (142 / 7)) for i, s in enumerate(SUPPORT)],
        "header_bottom": 68,   # 見出し行の下端（これより下が本体）
        "merged_cols": 4,      # 左から何列が縦に結合したセルか（仕様書・業務種別・業務内容・情報区分）。上の行の値を引き継ぐ
        "cell_cols": ["データ種別"],   # 縦に結合することがあるが、空欄もある列。空の行は、上の行との境目に線が無いときだけ上の値
    },
}


def hlines(page: pymupdf.Page) -> list[tuple[float, float, float]]:
    """横の罫線 (y, x0, x1)。線と、高さの小さい長方形の両方から。"""
    out = []
    for g in page.get_drawings():
        for it in g["items"]:
            if it[0] == "l" and abs(it[1].y - it[2].y) < 0.5:
                out.append((it[1].y, min(it[1].x, it[2].x), max(it[1].x, it[2].x)))
            elif it[0] == "re" and it[1].height < 1.5 and it[1].width > 3:
                out.append((it[1].y0 + it[1].height / 2, it[1].x0, it[1].x1))
            elif it[0] == "re" and it[1].height >= 1.5:   # 枠の長方形（網掛けの行など）は上下の辺を罫線とみなす
                out += [(it[1].y0, it[1].x0, it[1].x1), (it[1].y1, it[1].x0, it[1].x1)]
    return out


def column_cells(lines, x0, x1, top, bottom) -> list[tuple[float, float]]:
    """列の中央を横切る罫線で区切った、縦のセルの範囲。"""
    xm = (x0 + x1) / 2
    ys = sorted({round(y, 1) for y, a, b in lines if a - 0.5 <= xm <= b + 0.5 and top - 1 <= y <= bottom + 1})
    ys = [y for i, y in enumerate(ys) if i == 0 or y - ys[i - 1] > 2]   # 二重線をまとめる
    return list(zip(ys, ys[1:]))


def page_chars(page: pymupdf.Page) -> list[tuple[float, float, str]]:
    """1文字ずつ (x の中心, y の中心, 文字)。"""
    out = []
    for b in page.get_text("rawdict")["blocks"]:
        for ln in b.get("lines", []):
            for sp in ln["spans"]:
                for c in sp["chars"]:
                    if c["c"].strip():
                        x0, y0, x1, y1 = c["bbox"]
                        out.append(((x0 + x1) / 2, (y0 + y1) / 2, c["c"]))
    return out


def text_in(chars, x0, x1, y0, y1) -> str | None:
    cs = [c for c in chars if x0 <= c[0] < x1 and y0 <= c[1] < y1]
    if not cs:
        return None
    # 行（y の中心が 2pt 以内）ごとに、左から
    cs.sort(key=lambda c: c[1])
    lines, cur = [], [cs[0]]
    for c in cs[1:]:
        if c[1] - cur[-1][1] > 2:
            lines.append(cur)
            cur = []
        cur.append(c)
    lines.append(cur)
    s = "".join("".join(c[2] for c in sorted(ln)) for ln in lines)
    return unicodedata.normalize("NFKC", s).replace("〇", "○")


def extract_page(page: pymupdf.Page, lay: dict, carry: dict | None = None) -> list[dict]:
    chars = page_chars(page)
    lines = hlines(page)
    top = lay["header_bottom"]
    bottom = max(y for y, a, b in lines)
    cols = lay["columns"]
    # 行: No の列の文字の y（2pt 以内は同じ行）
    no_x0, no_x1 = next((x0, x1) for n, x0, x1 in cols if n == "No")
    ys = sorted(c[1] for c in chars if no_x0 <= c[0] < no_x1 and top < c[1] < bottom)
    anchors = []
    for y in ys:
        if not anchors or y - anchors[-1][-1] > 2:
            anchors.append([y])
        else:
            anchors[-1].append(y)
    mids = [sum(a) / len(a) for a in anchors]
    bands = []
    for i, m in enumerate(mids):
        up = (mids[i - 1] + m) / 2 if i else m - (mids[1] - m) / 2 if len(mids) > 1 else m - 4
        dn = (mids[i + 1] + m) / 2 if i + 1 < len(mids) else m + (m - mids[i - 1]) / 2 if i else m + 4
        bands.append((up, dn))
    # 縦に結合したセル（左から merged_cols 列）: その列を横切る罫線で区切った範囲
    merged = {name: column_cells(lines, x0, x1, top, bottom) for name, x0, x1 in cols[:lay["merged_cols"]]}
    # 罫線が図形として取れない所があるので、境目に線があるかは頁の画像の明るさで見る（線: 暗い / 結合したセルの中: 白）
    Z = 4
    pix = page.get_pixmap(matrix=pymupdf.Matrix(Z, Z), colorspace=pymupdf.csGRAY)

    def has_rule(y: float, x0: float, x1: float) -> bool:
        lum = 255.0
        for yy in range(int((y - 0.8) * Z), int((y + 0.8) * Z) + 1):
            row = [pix.pixel(x, yy)[0] for x in range(int(x0 * Z) + 2, int(x1 * Z) - 2)]
            lum = min(lum, sum(row) / len(row))
        return lum < 220
    carry = {} if carry is None else carry
    items = []
    for (y0, y1), ym in zip(bands, mids):
        vals = {}
        for name, x0, x1 in cols:
            if name in merged:
                c = next(((a, b) for a, b in merged[name] if a <= ym < b), (y0, y1))
                # 結合したセルの文字が上の行（前の頁を含む）にあるときは、上の行の値を引き継ぐ
                vals[name] = text_in(chars, x0, x1, *c) or carry.get(name)
                carry[name] = vals[name]
            elif name in lay.get("cell_cols", []):
                vals[name] = text_in(chars, x0, x1, y0, y1)
                if vals[name] is None and items and not has_rule(y0, x0, x1):
                    vals[name] = next(c["value"] for c in items[-1]["cells"] if c["column"] == name)
            else:
                vals[name] = text_in(chars, x0, x1, y0, y1)
        no = vals.pop("No")
        name = vals.pop("情報名")
        items.append({"no": int(no) if no and no.isdigit() else None, "no_raw": no, "name_path": [name] if name else [],
                      "type": None, "length": None, "length_raw": None, "content": None, "required": None,
                      "required_by": [{"column": c, "value": vals.pop(c)} for c, *_ in cols if c.startswith("対応業務")],
                      "note": None, "cells": [{"column": c, "value": v} for c, v in vals.items()]})
    return items


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="prod5-png-post")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    out_dir = ROOT / "out" / f"{args.run}-reviewed"
    man = load_manifest()
    for doc, lay in LAYOUTS.items():
        pdf = pymupdf.open(pdf_path(man[doc]))
        carry: dict = {}   # 縦に結合したセルの、直前の行の値（頁をまたいで引き継ぐ）
        for i, p in enumerate(lay["pages"]):
            f = out_dir / f"{doc}_p{p}.json"
            res = json.loads(f.read_text(encoding="utf-8"))
            items = extract_page(pdf[p - 1], lay, carry)
            old = [t for t in res["tables"] if t.get("table_kind") == lay["table_kind"]]
            if args.check:
                diff(p, items, old[0]["items"] if old else [])
                continue
            res["tables"] = [t for t in res["tables"] if t.get("table_kind") != lay["table_kind"]] + [{
                "table_kind": lay["table_kind"], "title": lay["title"], "record": {"exchange_id": "", "name": "", "parent": ""},
                "columns": [c for c, *_ in lay["columns"]],
                "column_map": {"no": "No", "name": "情報名", "type": "", "length": "", "content": "", "required": "", "note": ""},
                "items": items, "continued_from_prev_page": i > 0, "continues_to_next_page": p != lay["pages"][-1],
                "source_model": "textlayer"}]
            res["_fixes"] = [x for x in res.get("_fixes", []) if x.get("by") != "textlayer"]   # 何度実行しても同じに
            res["_fixes"].append({"by": "textlayer", "note": f"{lay['title']} を PDF のテキストレイヤから組み立てて差し替え（{len(items)} 行）"})
            f.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"{doc} p{p}: {len(items)} 行")
    if not args.check:
        # 頁をまたぐ表をつなぎ直す（apply_review.py と同じ）
        pages_by_doc: dict[str, list] = {}
        for f in sorted(out_dir.glob("*_p*.json")):
            r = json.loads(f.read_text(encoding="utf-8"))
            pages_by_doc.setdefault(r["doc_id"], []).append((r["page"], r))
        logical, joined = build_logical(pages_by_doc, {d: doc_profile(pdf_path(man[d])) for d in pages_by_doc})
        (out_dir / "logical_tables.json").write_text(json.dumps(logical, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"→ {out_dir.relative_to(ROOT)}/logical_tables.json（表 {len(logical)}、結合 {joined}）")
    return 0


def diff(p: int, new: list[dict], old: list[dict]) -> None:
    def flat(it):
        return {"No": it["no_raw"], "情報名": (it["name_path"] or [None])[-1],
                **{c["column"]: c["value"] for c in it["cells"]}, **{c["column"]: c["value"] for c in it["required_by"]}}
    n = lambda v: unicodedata.normalize("NFKC", v or "").replace(" ", "").replace("（", "(").replace("）", ")")
    o = {str(it["no_raw"]): flat(it) for it in old}
    print(f"p{p}: テキストレイヤ {len(new)} 行 / 確定版 {len(old)} 行")
    for it in new:
        a = flat(it)
        b = o.get(str(it["no_raw"]))
        if b is None:
            print(f"  No {it['no_raw']}: 確定版に無い")
            continue
        for k, v in a.items():
            kb = next((x for x in b if n(x) == n(k)), None)
            if kb is None or n(v) != n(b[kb]):
                print(f"  No {it['no_raw']} {k}: テキスト {v!r} / 確定版 {b.get(kb)!r}")


if __name__ == "__main__":
    sys.exit(main())
