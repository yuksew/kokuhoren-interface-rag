"""表ごとの交換情報識別番号（7111、J121 など）を、原本の文字と書き起こし結果から補う（API は使わない）。

手がかり（強い順。どれで決めたかを source に残す）
  self      表の中の「交換情報識別番号」の行に固定値が書いてある（介護: “7541”固定）
  model     モデルが record.exchange_id に入れた値
  columns   列見出しに識別番号がある（障害: 「※必須 J121 J131 J221」）
  section   同じ節（1.2.3.2. など）のほかの表の番号がすべて同じとき、それを共有する
  name      節の見出しを、同じ章のインタフェース一覧の情報名と照合した（一致率 0.8 以上）
  title     表題を、同じ章のインタフェース一覧の情報名と照合した（一致率 0.9 以上）
  residual  節に対応するインタフェース一覧の節の番号から、同じ節のほかの表が固定値で持つ番号を除いた残り
決められない表は空のままにする。
1つの表が複数の識別番号に対応することがある（同じレコード形式を複数の情報で使う）。
"""

from __future__ import annotations

import difflib
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent
HEAD = re.compile(r"^(\d+(?:\.\d+){2,})\.?\s*(\S.*)$")  # 1.2.3.2. 介護給付費等 明細書情報 / 2.3.1 ○○
APPENDIX = re.compile(r"^(付録\s*[.．]\s*[a-zA-Z0-9]+)\s*(\S.*)$")   # 付録．ａ エラーメッセージ一覧（インターネット編）
LEADER = re.compile(r"[.．…・]{4,}")   # 目次の行（「3.4.5.1 復号 ........ 42」）は見出しにしない
QUOTED = re.compile(r"[“\"”]\s*([0-9A-Z]{4})\s*[“\"”]")
COL_ID = re.compile(r"(?<![0-9A-Za-z])([A-Z][0-9][0-9A-Z][0-9])(?![0-9A-Za-z])")


def nk(s) -> str:
    return unicodedata.normalize("NFKC", str(s or ""))


def squash(s) -> str:
    s = re.sub(r"[\s・、，,（）()\[\]【】「」]", "", nk(s))
    return re.sub(r"\(入力情報\)|\(出力情報\)|入力情報|出力情報", "", s)


def page_headings(pdf: Path) -> dict[int, list[tuple[int, str, str]]]:
    """ページごとの節見出し [(行番号, 番号, 名前)]。"""
    out = {}
    with pymupdf.open(pdf) as d:
        for i, pg in enumerate(d):
            hs = []
            for j, ln in enumerate(pg.get_text().splitlines()):
                t = nk(ln).strip()
                m = HEAD.match(t) or APPENDIX.match(t)
                if m and len(m.group(2)) <= 60 and not re.match(r"^[\d.]+$", m.group(2)) and not LEADER.search(t):
                    hs.append((j, m.group(1), m.group(2).strip()))
            out[i + 1] = hs
    return out


def section_of(table: dict, heads: dict, pdf_lines: dict) -> tuple[str, str] | None:
    """表の最初のページで表より前にある最後の見出し。無ければ前のページへさかのぼる。"""
    p = table["page_from"]
    lines = pdf_lines[p]
    title = squash(table.get("title"))
    start = next((j for j, ln in enumerate(lines) if title and len(title) >= 4 and title[:12] in squash(ln)), None)
    if start is None:
        start = next((j for j, ln in enumerate(lines) if nk(ln).strip() == "項番"), len(lines))
    cand = [h for h in heads.get(p, []) if h[0] <= start]
    if cand:
        return cand[-1][1], cand[-1][2]
    for q in range(p - 1, 0, -1):
        if heads.get(q):
            return heads[q][-1][1], heads[q][-1][2]
    return None


def assign(tables: list[dict], items_by_table: dict) -> dict[int, dict]:
    """tables: [{table_id, doc_id, domain, page_from, title, table_kind, columns, record_exchange_id}]
    items_by_table: table_id → [{name, content, note, ids}]（ids はインタフェース一覧の「識別」列の値）
    戻り値: table_id → {"ids": [...], "source": str|None, "section_no": str|None, "section_name": str|None}"""
    by_doc = defaultdict(list)
    for t in tables:
        by_doc[t["doc_id"]].append(t)
    result: dict[int, dict] = {}
    for doc, ts in by_doc.items():
        pdf = ROOT / "sources" / "raw" / ts[0]["domain"] / f"{doc}.pdf"
        heads = page_headings(pdf)
        with pymupdf.open(pdf) as d:
            pdf_lines = {i + 1: pg.get_text().splitlines() for i, pg in enumerate(d)}
        for t in ts:
            sec = section_of(t, heads, pdf_lines)
            r = {"ids": set(), "source": None, "section_no": sec[0] if sec else None, "section_name": sec[1] if sec else None}
            if t.get("table_kind") == "interface_list":
                result[t["table_id"]] = r
                continue
            for it in items_by_table.get(t["table_id"], []):
                if "交換情報識別番号" in nk(it.get("name")):
                    r["ids"] |= set(QUOTED.findall(nk(f"{it.get('content') or ''} {it.get('note') or ''}")))
            if r["ids"]:
                r["source"] = "self"
            elif t.get("record_exchange_id"):
                r["ids"], r["source"] = {t["record_exchange_id"]}, "model"
            else:
                ids = set(COL_ID.findall(nk(" ".join(t.get("columns") or []))))
                if ids:
                    r["ids"], r["source"] = ids, "columns"
            result[t["table_id"]] = r

        # 同じ節の表の識別番号がすべて同じなら、番号の無い表にも当てはめる
        sec_sets: dict[str, list[frozenset]] = defaultdict(list)
        for t in ts:
            r = result[t["table_id"]]
            if r["ids"] and r["section_no"]:
                sec_sets[r["section_no"]].append(frozenset(r["ids"]))
        # インタフェース一覧の情報名 → 識別番号（章ごと。障害は 1章 J・2章 K・3章 L のように章で分かれる）
        names: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
        for t in ts:
            if t.get("table_kind") != "interface_list":
                continue
            ch = (result[t["table_id"]]["section_no"] or "").split(".")[0]
            for it in items_by_table.get(t["table_id"], []):
                if it.get("name") and it.get("ids"):
                    names[ch][it["name"]] |= set(it["ids"])
        for t in ts:
            r = result[t["table_id"]]
            if r["ids"] or t.get("table_kind") not in ("record_layout", "required_matrix"):
                continue
            sets = sec_sets.get(r["section_no"]) or []
            if sets and len(set(sets)) == 1:
                r["ids"], r["source"] = set(sets[0]), "section"
            elif r["section_name"] and not sets:
                key = squash(r["section_name"])
                best, score = None, 0.0
                for name, ids in names.get((r["section_no"] or "").split(".")[0], {}).items():
                    sc = difflib.SequenceMatcher(None, key, squash(name)).ratio()
                    if sc > score:
                        best, score = ids, sc
                # 表題に「（複数児童）」のような限定があれば、それを含む情報名を優先する
                title = squash(t.get("title"))
                for name, ids in names.get((r["section_no"] or "").split(".")[0], {}).items():
                    qual = [squash(x) for x in re.findall(r"[（(]([^）)]+)[）)]", nk(name))]
                    base = squash(re.sub(r"[（(][^）)]+[）)]", "", nk(name)))
                    if qual and all(q and q in title for q in qual) and difflib.SequenceMatcher(None, key, base).ratio() >= 0.8:
                        best, score = ids, 1.0
                if best and score >= 0.8:
                    r["ids"], r["source"] = set(best), "name"
        # 残り: 表題が情報名と一致すればその番号（title）。
        # それでも無ければ、節に対応するインタフェース一覧の節の番号から、同じ節のほかの表が固定値で持つ番号を除いた残り（residual）。
        # 例: 介護 2.3.1 介護給付費請求書情報 ↔ 2.2.1 介護給付費請求情報。請求書の表が 7111/7112/7113/7121 を持つので、
        #     明細書のレコード（基本情報・明細情報など）は残りの明細書の番号（7131〜71R1）に対応する。
        if_secs: dict[str, dict] = defaultdict(lambda: {"name": "", "ids": set(), "names": defaultdict(set)})
        for t in ts:
            if t.get("table_kind") != "interface_list":
                continue
            rr = result[t["table_id"]]
            sec = if_secs[rr["section_no"] or ""]
            sec["name"] = rr["section_name"] or ""
            for it in items_by_table.get(t["table_id"], []):
                if it.get("ids"):
                    sec["ids"] |= set(it["ids"])
                    if it.get("name"):
                        sec["names"][it["name"]] |= set(it["ids"])
        self_ids: dict[str, set[str]] = defaultdict(set)
        for t in ts:
            rr = result[t["table_id"]]
            if rr["source"] == "self" and rr["section_no"]:
                self_ids[rr["section_no"]] |= set(rr["ids"])
        for t in ts:
            r = result[t["table_id"]]
            if r["ids"] or t.get("table_kind") not in ("record_layout", "required_matrix"):
                continue
            ch = (r["section_no"] or "").split(".")[0]
            title = squash(re.sub(r"^\s*[（(]\s*\d+\s*[）)]", "", nk(t.get("title"))))
            best, score = None, 0.0
            for sno, sec in if_secs.items():
                if sno.split(".")[0] != ch:
                    continue
                for name, ids in sec["names"].items():
                    sc = difflib.SequenceMatcher(None, title, squash(name)).ratio() if title else 0
                    if sc > score:
                        best, score = ids, sc
            if best and score >= 0.9:
                r["ids"], r["source"] = set(best), "title"
                continue
            claimed = self_ids.get(r["section_no"] or "")
            if not claimed or not r["section_name"]:
                continue
            key = squash(r["section_name"])
            cand = [(difflib.SequenceMatcher(None, key, squash(sec["name"])).ratio(), sno) for sno, sec in if_secs.items()
                    if sno.split(".")[0] == ch and sec["ids"]]
            if cand:
                sc, sno = max(cand)
                rest = if_secs[sno]["ids"] - claimed
                if sc >= 0.85 and rest and claimed <= if_secs[sno]["ids"]:
                    r["ids"], r["source"] = rest, "residual"
    for r in result.values():
        r["ids"] = sorted(r["ids"])
    return result
