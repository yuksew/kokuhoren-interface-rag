"""算定ルール資料（告示・留意事項・記載要領・Q&A・サービスコード表）を DB に入れる（API は使わない）。

usage: uv run python src/build_rules.py [--db db/interface_spec.sqlite]
  前提: build_db.py（DB を作り直す）→ これ → build_index.py
  入力: sources/rules_manifest.yaml と sources/raw/rules/（src/fetch.py --manifest sources/rules_manifest.yaml）
DB に作るもの:
  rule_docs      資料ごとの版・施行日・URL（manifest の写し）
  rule_units     本文のまとまり（見出しごと・ページごと）。新旧対照表は「改正後」（左の欄）だけ
  service_codes  サービスコード表（Excel）の1行1コード

新旧対照表の扱い: 「新／旧」「改正後／現行」の見出しがある資料の横長のページで、左右の両方に文字がある場合は左（新・改正後）だけを使う。
  右（旧・現行）を入れると、改正前の規定を今の規定として答えるおそれがあるため。
  留意事項・改正告示は見出しが無いページもあるので、横長で左右の両方に文字があれば新旧とみなす。
"""

from __future__ import annotations

import argparse
import html as htmlmod
import io
import json
import re
import sqlite3
import sys
import unicodedata
import zipfile
from pathlib import Path

import openpyxl
import pymupdf
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prose import PAGE_NO  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "sources" / "raw" / "rules"
# 新旧対照表の見出し（「新」「旧」、「改 正 後」「現 行」「改正前」）。どの種類の資料でも、これがあれば左右2欄として扱う
SHINKYU = [re.compile(r"^新\s*$"), re.compile(r"^旧\s*$"), re.compile(r"^改\s*正\s*後\s*$"), re.compile(r"^(現\s*行|改\s*正\s*前)\s*$")]


def is_shinkyu(path: Path) -> bool:
    """横長のページの上の方に「新」と「旧」（または「改正後」と「現行・改正前」）の見出しがあれば新旧対照表"""
    with pymupdf.open(path) as d:
        for pg in d:
            if pg.rect.width <= pg.rect.height:
                continue
            top = [nk(ln).strip() for ln in pg.get_text(clip=pymupdf.Rect(0, 0, pg.rect.width, pg.rect.height * 0.3)).splitlines()]
            hit = [any(p.match(ln) for ln in top) for p in SHINKYU]
            if (hit[0] and hit[1]) or (hit[2] and hit[3]):
                return True
    return False
# 見出しの行（本文のまとまりの区切り）。告示・留意事項の「１ 訪問介護費」「(4) 2人の訪問介護員等…」、Q&A の「【訪問介護】」「問３」
HEADS = [
    re.compile(r"^【[^】]{2,30}】$"),
    re.compile(r"^第[0-9一二三四五六七八九十]+(の[0-9]+)?\s+(?![号条項])[^\s。]{2,40}$"),
    re.compile(r"^[0-9]{1,2}(の[0-9]+)?\s+\S.{1,30}(費|加算|減算|について)$"),
    re.compile(r"^(問|Q)\s?[0-9]+(?:[-‐－の][0-9]+)?"),
]


def nk(s) -> str:
    return unicodedata.normalize("NFKC", str(s if s is not None else ""))


def join_lines(lines: list[str]) -> str:
    """PDF の改行をつなぐ。空白を入れるのは、英数字どうし（英単語・数字の区切り）のときだけ。
    「概ね」＋改行＋「2時間」のような日本語と数字の間に空白を入れると、全文検索で「2時間以上」が引けなくなる。"""
    out = ""
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        if out and re.match(r"[0-9A-Za-z]", out[-1]) and re.match(r"[0-9A-Za-z]", ln[0]):
            out += " "
        out += ln
    # PDF の文字データ自体に「2 時間」「1 日」のような空白があるので、数字と日本語の間の空白を消す
    out = re.sub(r"(?<=[0-9])[ \u3000]+(?=[^\x00-\x7F])|(?<=[^\x00-\x7F])[ \u3000]+(?=[0-9])", "", out)
    return re.sub(r"\s{2,}", " ", out)


def head_level(line: str) -> int | None:
    s = nk(line).strip()
    if len(s) > 60 or s.endswith("。"):
        return None
    for i, p in enumerate(HEADS):
        if p.match(s):
            return i
    return None


# ---------------------------------------------------------------- 本文
def pdf_pages(path: Path, two_col: bool) -> list[tuple[int, str, list[str]]]:
    """[(page, side, lines)]。side は full | new（新旧対照表の左の欄）"""
    out = []
    with pymupdf.open(path) as d:
        for i, pg in enumerate(d):
            r = pg.rect
            side = "full"
            clip = None
            if two_col and r.width > r.height:
                mid = r.x0 + r.width / 2
                left = len(pg.get_text(clip=pymupdf.Rect(r.x0, r.y0, mid, r.y1)).strip())
                right = len(pg.get_text(clip=pymupdf.Rect(mid, r.y0, r.x1, r.y1)).strip())
                if left > 0 and right > 0 and min(left, right) / max(left, right) > 0.15:
                    clip, side = pymupdf.Rect(r.x0, r.y0, mid, r.y1), "new"
            lines = [ln for ln in pg.get_text(clip=clip).splitlines() if ln.strip() and not PAGE_NO.match(nk(ln).strip())]
            out.append((i + 1, side, lines))
    return out


def html_pages(path: Path) -> list[tuple[int, str, list[str]]]:
    """法令等データベースの HTML（fetch.py が <!-- page N --> でつないだもの）→ ページごとの行"""
    out = []
    parts = re.split(r"<!-- page (\d+) -->\n", path.read_text(encoding="utf-8"))
    for no, body in zip(parts[1::2], parts[2::2]):
        body = re.sub(r"(?is)<(script|style|head)\b.*?</\1>", " ", body)
        body = re.sub(r"(?i)<br\s*/?>|</(p|div|tr|li|h\d)>", "\n", body)
        text = htmlmod.unescape(re.sub(r"<[^>]+>", " ", body))
        lines = [re.sub(r"[ \t　]+", " ", ln).strip() for ln in text.splitlines()]
        lines = [ln for ln in lines if ln]
        # 本文は最初の「○」（告示の題名）から。ページ移動・添付一覧などの画面部品を外す
        start = next((i for i, ln in enumerate(lines) if ln.startswith("○")), 0) if no == "1" else 0
        lines = [ln for ln in lines[start:] if not re.match(r"^(添付一覧|添付画像はありません|該当ページ数|＜ページ移動＞|[0-9 ]+$|ページ中)", ln)]
        out.append((int(no), "full", lines))
    return out


def units(pages: list[tuple[int, str, list[str]]], size: int = 800) -> list[dict]:
    """見出しの行で区切り、size 文字までまとめる。見出しはページをまたいで引き継ぐ。"""
    out = []
    heads: dict[int, str] = {}
    for page, side, lines in pages:
        cur: list[str] = []

        def flush():
            text = join_lines([nk(x) for x in cur])  # NFKC: 全角の数字・英字をそろえる（質問も NFKC で検索する）
            if len(text) >= 30:
                path = " > ".join(heads[k] for k in sorted(heads))
                for piece in chop(text, size):
                    out.append({"page": page, "side": side, "heading": path or None, "text": piece})
            cur.clear()

        for ln in lines:
            lv = head_level(ln)
            if lv is not None:
                flush()
                heads[lv] = nk(ln).strip()[:50]
                for k in [k for k in heads if k > lv]:
                    del heads[k]
            cur.append(ln)
            if sum(len(x) for x in cur) > size * 1.5:
                flush()
        flush()
    # 短いまとまりは、同じページ・同じ見出しの次のまとまりとくっつける
    merged: list[dict] = []
    for u in out:
        p = merged[-1] if merged else None
        if p and p["page"] == u["page"] and p["heading"] == u["heading"] and len(p["text"]) + len(u["text"]) <= size:
            p["text"] += " " + u["text"]
        else:
            merged.append(dict(u))
    return merged


def chop(text: str, size: int) -> list[str]:
    if len(text) <= size:
        return [text]
    sents = [s for s in re.split(r"(?<=。)", text) if s]
    out, cur = [], ""
    for s in sents:
        while len(s) > size:
            out.append(cur + s[: size - len(cur)])
            s, cur = s[size - len(cur):], ""
        if len(cur) + len(s) > size:
            out.append(cur)
            cur = ""
        cur += s
    if cur.strip():
        out.append(cur)
    return [x.strip() for x in out if x.strip()]


# ---------------------------------------------------------------- サービスコード表
def workbooks(path: Path):
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as z:
            for n in z.namelist():
                if n.lower().endswith(".xlsx"):
                    yield openpyxl.load_workbook(io.BytesIO(z.read(n)), read_only=True, data_only=True)
    elif path.suffix == ".xlsx":
        yield openpyxl.load_workbook(path, read_only=True, data_only=True)


def fmt(v) -> str:
    if isinstance(v, float):
        return f"{v * 100:g}%" if 0 < v < 1 else f"{v:g}"
    return nk(v).strip()


def service_rows(path: Path) -> list[dict]:
    out = []
    for wb in workbooks(path):
        for ws in wb.worksheets:
            rows = list(ws.iter_rows(values_only=True))
            hdr = next((i for i, r in enumerate(rows[:30]) if any(nk(c).strip() == "サービスコード" for c in r if c is not None)), None)
            if hdr is None or hdr + 1 >= len(rows):
                continue
            h1, h2 = rows[hdr], rows[hdr + 1]
            col = lambda r, name: next((j for j, c in enumerate(r) if c is not None and re.sub(r"\s", "", nk(c)) == name), None)  # noqa: E731
            c_kind, c_item = col(h2, "種類"), col(h2, "項目")
            c_name, c_units, c_unit = col(h1, "サービス内容略称"), col(h2, "単位数"), col(h2, "単位")
            if None in (c_kind, c_item, c_name, c_units):
                print(f"  ! 見出しの列が分からないシート: {path.name} / {ws.title}", file=sys.stderr)
                continue
            title = next((nk(c).strip() for r in rows[:hdr] for c in r if c is not None and "サービスコード表" in nk(c)), None)
            service = re.sub(r"^[0-9]+\s*", "", title or ws.title.strip())
            unit = None
            for i, r in enumerate(rows[hdr + 2:], hdr + 3):
                k, it = r[c_kind] if c_kind < len(r) else None, r[c_item] if c_item < len(r) else None
                if k is None or it is None:
                    continue
                kind = nk(k).strip().zfill(2) if isinstance(k, int) else nk(k).strip()
                item = f"{it:04d}" if isinstance(it, int) else nk(it).strip()
                if not re.fullmatch(r"[0-9A-Z]{2}", kind) or not re.fullmatch(r"[0-9A-Z]{4}", item):
                    continue
                if c_unit is not None and c_unit < len(r) and r[c_unit] is not None:
                    unit = fmt(r[c_unit])
                cond = [fmt(c) for c in r[c_name + 1:c_units] if c is not None and fmt(c)]
                out.append({"sheet": ws.title.strip(), "row": i, "service": service, "kind_code": kind, "item_code": item,
                            "name": fmt(r[c_name]) if r[c_name] is not None else None,
                            "units": fmt(r[c_units]) if c_units < len(r) and r[c_units] is not None else None,
                            "unit": unit, "conditions": " ".join(cond) or None})
    return out


SCHEMA = """
DROP TABLE IF EXISTS rule_docs;
CREATE TABLE rule_docs (doc_id TEXT PRIMARY KEY, domain TEXT NOT NULL, category TEXT NOT NULL, title TEXT, edition TEXT,
                        effective TEXT, url TEXT, source_page TEXT, sha256 TEXT, file TEXT, note TEXT);
DROP TABLE IF EXISTS rule_units;
CREATE TABLE rule_units (unit_id INTEGER PRIMARY KEY, doc_id TEXT NOT NULL REFERENCES rule_docs, page INTEGER,
                         side TEXT NOT NULL,   -- full | new（新旧対照表の改正後の欄）
                         heading TEXT, text TEXT NOT NULL);
DROP TABLE IF EXISTS service_codes;
CREATE TABLE service_codes (sc_id INTEGER PRIMARY KEY, doc_id TEXT NOT NULL REFERENCES rule_docs, sheet TEXT, row INTEGER,
                            service TEXT, kind_code TEXT NOT NULL, item_code TEXT NOT NULL, code TEXT NOT NULL,
                            name TEXT, units TEXT, unit TEXT, conditions TEXT);
CREATE INDEX ix_sc_code ON service_codes(code);
"""


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="db/interface_spec.sqlite")
    args = ap.parse_args()
    entries = yaml.safe_load((ROOT / "sources" / "rules_manifest.yaml").read_text(encoding="utf-8"))
    log = json.loads((ROOT / "sources" / "fetch_log.rules.json").read_text(encoding="utf-8"))
    con = sqlite3.connect(ROOT / args.db)
    con.executescript(SCHEMA)
    n_units = n_codes = 0
    for e in entries:
        if e.get("status") == "future" or e["id"] not in log:
            continue
        f = ROOT / log[e["id"]]["file"]
        con.execute("INSERT INTO rule_docs VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (e["id"], e["domain"], e["category"], e["title"], e.get("edition"), str(e["effective"]) if e.get("effective") else None,
                     e["url"], e.get("source_page"), log[e["id"]]["sha256"], log[e["id"]]["file"], e.get("note")))
        if e.get("ingest") == "prose":
            pages = html_pages(f) if f.suffix == ".html" else pdf_pages(f, e["category"] in ("ryui", "kokuji_kaisei") or (e["category"] not in ("kozo", "servicecode") and is_shinkyu(f)))
            us = units(pages)
            con.executemany("INSERT INTO rule_units (doc_id, page, side, heading, text) VALUES (?,?,?,?,?)",
                            [(e["id"], u["page"], u["side"], u["heading"], u["text"]) for u in us])
            n_new = sum(1 for p in pages if p[1] == "new")
            print(f"本文 {e['id']}: {len(pages)} ページ（新旧の左欄だけ {n_new}）→ {len(us)} まとまり")
            n_units += len(us)
        elif e.get("ingest") == "table" and f.suffix in (".zip", ".xlsx"):
            rows = service_rows(f)
            con.executemany("INSERT INTO service_codes (doc_id, sheet, row, service, kind_code, item_code, code, name, units, unit, conditions) "
                            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                            [(e["id"], r["sheet"], r["row"], r["service"], r["kind_code"], r["item_code"], r["kind_code"] + r["item_code"],
                              r["name"], r["units"], r["unit"], r["conditions"]) for r in rows])
            print(f"コード {e['id']}: {len(rows)} 行（{len({r['sheet'] for r in rows})} シート）")
            n_codes += len(rows)
    con.execute("INSERT OR REPLACE INTO build_info VALUES ('rules_built', datetime('now'))")
    con.commit()
    print(f"→ rule_docs / rule_units {n_units} / service_codes {n_codes}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
