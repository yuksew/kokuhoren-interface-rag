"""確認キューの判定を採用版に当てはめる共通処理（review_app.py と apply_review.py が使う）。

判定ファイル reports/review_decisions.{run}.json
  {"items": {キューID: {"action": ..., "value": ..., "at": ...}},
   "cells": {"doc|page|表|行|列番号": {"value": ..., "no": 項番, "at": ...}}}

action
  haiku   Haiku の値のまま（行の場合: Haiku にだけある行は残す／Sonnet にだけある行は追加しない）
  sonnet  Sonnet の値にする（行の場合: Sonnet にだけある行を追加する）
  edit    value の値にする（列名の場合は「 | 」区切り）
  delete  行を削除する
  manual  セルを個別に直した（cells 側の値を使う）
  hold    保留（Haiku のまま。あとで見直す）
cells の「行」は採用版での行番号（ia）。Sonnet から追加した行は "q:キューID"。
"""

from __future__ import annotations

import copy
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRIMARY, SECOND = "claude-haiku-5-5", "claude-sonnet-5-5"
STD_FIELDS = ["no", "name", "type", "length", "content", "required", "note"]
FIELD_LABEL = {"no": "項番", "name": "項目名", "type": "属性", "length": "桁数", "content": "内容", "required": "必須", "note": "備考"}
FIELD_LABEL_EXTRA = {"cells": "その他の列", "required_by": "必須（列別）", "row": "行", "columns": "列名", "page": "ページ"}
DONE = {"haiku", "sonnet", "edit", "delete", "manual"}


def norm(s) -> str:
    if s is None:
        return ""
    s = unicodedata.normalize("NFKC", str(s)).replace("◯", "○").replace("〇", "○")
    return re.sub(r"\s+", "", s)


def col_key(c) -> str:
    c = unicodedata.normalize("NFKC", str(c or ""))
    m = re.search(r"(?<!\d)\d{4}(?!\d)", c)
    return m.group(0) if m else norm(c.split(">")[-1])


# ---------- 入出力 ----------

def paths(run: str) -> dict:
    return {
        "adopted": ROOT / "out" / f"{run}-adopted",
        "sonnet": ROOT / "out" / run / SECOND,
        "queue": ROOT / "reports" / f"review_queue.{run}.json",
        "decisions": ROOT / "reports" / f"review_decisions.{run}.json",
        "reviewed": ROOT / "out" / f"{run}-reviewed",
    }


def load_queue(run: str) -> list[dict]:
    return json.loads(paths(run)["queue"].read_text(encoding="utf-8"))


def load_decisions(run: str) -> dict:
    f = paths(run)["decisions"]
    d = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    d.setdefault("items", {})
    d.setdefault("cells", {})
    return d


def save_decisions(run: str, d: dict) -> None:
    f = paths(run)["decisions"]
    tmp = f.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(f)


def load_page(run: str, doc: str, page: int) -> tuple[dict, dict | None]:
    p = paths(run)
    adopted = json.loads((p["adopted"] / f"{doc}_p{page}.json").read_text(encoding="utf-8"))
    sf = p["sonnet"] / f"{doc}_p{page}.json"
    sonnet = json.loads(sf.read_text(encoding="utf-8"))["result"] if sf.exists() else None
    return adopted, sonnet


# ---------- 列とセル ----------

_GUESS = [("no", r"^(項番|No|NO|番号)$"), ("name", r"項目名|^項目$|情報名"), ("type", r"属性"), ("length", r"桁"),
          ("content", r"^内容|説明"), ("required", r"^必須"), ("note", r"^備考")]


def col_field(table: dict, col: str) -> str | None:
    """列名が決まった欄（項番・項目名など）のどれに当たるか。どれでもなければ None（cells / required_by の列）。"""
    cm = table.get("column_map") or {}
    for f in STD_FIELDS:
        if cm.get(f) and norm(cm[f]) == norm(col):
            return f
    if any(cm.get(f) for f in STD_FIELDS):
        return None
    for f, pat in _GUESS:  # column_map が空のときだけ列名から推測する
        if re.search(pat, norm(col)):
            return f
    return None


def table_columns(table: dict) -> list[str]:
    cols = list(table.get("columns") or [])
    if cols:
        return cols
    items = table.get("items") or []
    cols = [FIELD_LABEL[f] for f in STD_FIELDS if any(get_field(it, f) not in (None, "") for it in items)]
    extra = []
    for it in items:
        for c in (it.get("required_by") or []) + (it.get("cells") or []):
            if c.get("column") and c["column"] not in extra:
                extra.append(c["column"])
    return cols + extra


def get_field(it: dict, f: str):
    if f == "no":
        return it.get("no_raw") or (str(it["no"]) if it.get("no") is not None else None)
    if f == "name":
        return " > ".join(it.get("name_path") or []) or None
    if f == "length":
        return it.get("length_raw") or (str(it["length"]) if it.get("length") is not None else None)
    v = it.get(f)
    return None if v is None else str(v)


def set_field(it: dict, f: str, v) -> None:
    v = None if v in (None, "") else str(v)
    if f == "no":
        it["no_raw"] = v
        it["no"] = int(norm(v)) if v and norm(v).isdigit() else it.get("no")
    elif f == "name":
        it["name_path"] = [x.strip() for x in v.split(">")] if v else []
    elif f == "length":
        it["length_raw"] = v
        it["length"] = int(norm(v)) if v and norm(v).isdigit() else None
    else:
        it[f] = v


def _find_entry(it: dict, col: str, pos: int | None = None):
    for key in ("cells", "required_by"):
        for e in it.get(key) or []:
            if e.get("column") == col:
                return e
    k = col_key(col)
    for key in ("cells", "required_by"):
        for e in it.get(key) or []:
            if col_key(e.get("column")) == k:
                return e
    return None


def get_cell(table: dict, it: dict, col: str):
    f = col_field(table, col)
    if f:
        return get_field(it, f)
    e = _find_entry(it, col)
    return None if e is None or e.get("value") in (None, "") else str(e["value"])


def set_cell(table: dict, it: dict, col: str, v) -> None:
    f = col_field(table, col)
    if f:
        set_field(it, f, v)
        return
    e = _find_entry(it, col)
    if e is None:
        key = "required_by" if it.get("required_by") and not it.get("cells") else "cells"
        e = {"column": col, "value": None}
        it.setdefault(key, []).append(e)
    e["value"] = None if v in (None, "") else str(v)


def other_cell(h_table: dict, col: str, s_table: dict | None, s_item: dict | None):
    """Haiku の列名 col に当たる Sonnet の値（列名の書き方の違いは列番号・様式番号で吸収）。"""
    if s_item is None:
        return None
    f = col_field(h_table, col)
    if f and get_field(s_item, f) not in (None, ""):
        return get_field(s_item, f)
    # 同じ列の値を、もう一方のモデルが別の欄（required と required_by、cells など）に入れていることがある
    e = _find_entry(s_item, col)
    if e is not None and e.get("value") not in (None, ""):
        return str(e["value"])
    if s_table is not None:
        sf = next((x for x in STD_FIELDS if (s_table.get("column_map") or {}).get(x) and col_key(s_table["column_map"][x]) == col_key(col)), None)
        if sf and get_field(s_item, sf) not in (None, ""):
            return get_field(s_item, sf)
    # 原本の1列（例「※必須 J121 J131 J221」）を、もう一方が複数の列に分けた場合
    nc = norm(col)
    parts = [e for key in ("required_by", "cells") for e in s_item.get(key) or []
             if e.get("value") not in (None, "") and norm(str(e.get("column") or "").split(">")[-1]) in nc
             and norm(str(e.get("column") or "").split(">")[-1])]
    if parts:
        vals = list(dict.fromkeys(str(e["value"]) for e in parts))
        return vals[0] if len(vals) == 1 else " / ".join(vals)
    return None


MARK_FIELDS = {"cells", "required_by", "required"}


def compare_cols(h_table: dict, h_item: dict, s_table: dict | None, s_item: dict | None, field: str, cols: list[str] | None = None):
    """項目の1つの欄について、列ごとに Haiku と Sonnet の値を並べる。戻り値: (食い違う列番号, Haiku の値, Sonnet の値)。"""
    cols = cols if cols is not None else table_columns(h_table)
    diff, hv, sv = [], {}, {}
    for ci, c in enumerate(cols):
        f = col_field(h_table, c)
        if field in MARK_FIELDS:
            if f is not None and not (f == "required" or field == "required" and f is None):
                continue
        elif f != field:
            continue
        a, b = get_cell(h_table, h_item, c), other_cell(h_table, c, s_table, s_item)
        if a is None and b is None:
            continue
        hv[ci], sv[ci] = a, b
        if norm(a) != norm(b):
            diff.append(ci)
    return diff, hv, sv


# ---------- 判定の当てはめ ----------

FIELD_SRC = {"name": ["name_path"], "length": ["length", "length_raw"], "cells": ["cells"], "required_by": ["required_by"]}


def _record(it: dict, fields: list[str], before: dict, qid: str) -> None:
    for f in fields:
        if before.get(f) != it.get(f):
            it.setdefault("_fixes", []).append({"field": f, "from": before.get(f), "to": copy.deepcopy(it.get(f)), "by": "human", "qid": qid})


def apply_page(adopted: dict, sonnet: dict | None, items: list[dict], dec: dict, final: bool) -> dict:
    """1ページ分の採用版に判定を当てはめる。final=False のときは削除・追加を消さずに印を付ける（画面表示用）。"""
    page = copy.deepcopy(adopted)
    s_tables = (sonnet or {}).get("tables") or []
    for t in page.get("tables") or []:
        for i, it in enumerate(t.get("items") or []):
            it["_ia"] = i
    doc, pg = page["doc_id"], page["page"]

    def s_item(q):
        try:
            return s_tables[q["table"]]["items"][q["ib"]]
        except (IndexError, KeyError, TypeError):
            return None

    # 1) 列名
    for q in items:
        d = dec["items"].get(q["id"])
        if q["field"] != "columns" or not d or d["action"] not in ("sonnet", "edit"):
            continue
        t = page["tables"][q["table"]]
        old = list(t.get("columns") or [])
        new = [x.strip() for x in (d.get("value") or "").split("|")] if d["action"] == "edit" else \
            list((s_tables[q["table"]].get("columns") or []) if q["table"] < len(s_tables) else old)
        if len(new) == len(old):  # 位置で対応づけて、セル・column_map の列名も書き換える
            ren = dict(zip(old, new))
            for it in t.get("items") or []:
                for e in (it.get("cells") or []) + (it.get("required_by") or []):
                    e["column"] = ren.get(e.get("column"), e.get("column"))
            t["column_map"] = {k: ren.get(v, v) for k, v in (t.get("column_map") or {}).items()}
        t["columns"] = new
        t.setdefault("_fixes", []).append({"field": "columns", "from": old, "to": new, "by": "human", "qid": q["id"]})

    # 2) セルの値（項目ごと）
    for q in items:
        d = dec["items"].get(q["id"])
        if not d or q["field"] in ("columns", "row", "page") or q.get("ia") is None:
            continue
        t = page["tables"][q["table"]]
        it = t["items"][q["ia"]]
        src = FIELD_SRC.get(q["field"], [q["field"]])
        if q["field"] in MARK_FIELDS:
            src = ["required", "required_by", "cells"]
        before = {f: copy.deepcopy(it.get(f)) for f in src}
        if d["action"] == "sonnet" and q["field"] in MARK_FIELDS:
            # 欄の入れ方は Haiku のままにして、列ごとに Sonnet の値を入れる
            st = s_tables[q["table"]] if q["table"] < len(s_tables) else None
            cols = table_columns(t)
            _, _, sv = compare_cols(t, it, st, s_item(q), q["field"], cols)
            for ci, v in sv.items():
                set_cell(t, it, cols[ci], v)
        elif d["action"] == "sonnet" and s_item(q) is not None:
            for f in src:
                it[f] = copy.deepcopy(s_item(q).get(f))
        elif d["action"] == "edit" and q["field"] not in ("cells", "required_by"):
            set_field(it, q["field"], d.get("value"))
        _record(it, src, before, q["id"])

    # 3) Sonnet にだけある行の追加（判定前は表示用に薄く出す）
    for q in items:
        if q["field"] != "row" or q.get("ib") is None:
            continue
        d = dec["items"].get(q["id"])
        add = d is not None and d["action"] == "sonnet"
        if final and not add:
            continue
        si = s_item(q)
        if si is None:
            continue
        t = page["tables"][q["table"]]
        new = copy.deepcopy(si)
        new.update({"_ia": None, "_qid": q["id"], "_added": add, "_ghost": not add,
                    "_fixes": [{"field": "row", "from": None, "to": "Sonnet の行を追加", "by": "human", "qid": q["id"]}] if add else []})
        lst = t.setdefault("items", [])
        pos = next((i for i, x in enumerate(lst) if x.get("no") is not None and new.get("no") is not None and x["no"] > new["no"]), len(lst))
        lst.insert(pos, new)

    # 4) セルの個別修正
    for key, c in dec["cells"].items():
        kd, kp, kt, kr, kc = key.split("|")
        if kd != doc or int(kp) != pg:
            continue
        t = page["tables"][int(kt)]
        cols = table_columns(t)
        it = next((x for x in t.get("items") or [] if (f"q:{x['_qid']}" if x.get("_qid") else str(x.get("_ia"))) == kr), None)
        if it is None or int(kc) >= len(cols):
            continue
        before = {"value": get_cell(t, it, cols[int(kc)])}
        set_cell(t, it, cols[int(kc)], c.get("value"))
        if before["value"] != get_cell(t, it, cols[int(kc)]):
            it.setdefault("_fixes", []).append({"field": cols[int(kc)], "from": before["value"], "to": c.get("value"), "by": "human"})

    # 5) 削除
    for q in items:
        d = dec["items"].get(q["id"])
        if q["field"] == "row" and q.get("ia") is not None and d and d["action"] == "delete":
            t = page["tables"][q["table"]]
            it = next(x for x in t["items"] if x.get("_ia") == q["ia"])
            it["_deleted"] = True

    if final:
        for t in page.get("tables") or []:
            t["items"] = [x for x in t.get("items") or [] if not x.get("_deleted")]
            for x in t["items"]:
                for k in ("_ia", "_qid", "_added", "_ghost", "_deleted"):
                    x.pop(k, None)
                if not x.get("_fixes"):
                    x.pop("_fixes", None)
    return page
