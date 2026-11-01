"""書き起こし結果の自動チェック。

チェック内容:
  1. 項番が連番か（前ページからの続きでなければ 1 始まり。結合行による同一項番の繰り返しは許容）
  2. 桁数（バイト数）が整数か（record_layout / code_list で null は警告）
  3. 必須記号が想定の値（◎ ○ △ / 空欄）か
  4. 属性が既知の値か
  5. PDF テキストレイヤとの照合: 項目名・内容・備考の文字列がページのテキストに存在するか
     （存在しない＝読み違い・補完・幻覚の疑い。ただし図中の文字などテキストレイヤに無いものもある）
  6. ページをまたぐ表の連続性（config/pages.yaml の pair）
  7. モデル間の食い違い（項番で行を対応づけ、列ごとに比較）

usage: uv run python src/validate.py [--run anthropic-png]
出力: out/{run}/validation.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

import pymupdf
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pagemeta import doc_profile  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
REQUIRED_MARKS = {"◎", "○", "△"}
KNOWN_TYPES = {"数字", "英数", "漢字", "数値", "コード値", "英数カナ", "カナ", "日付", "全角", "半角", "英字", "英数字"}
COMPARE_FIELDS = ["name", "type", "length", "content", "required", "required_by", "note"]
TEXT_FIELDS = ["name", "content", "note"]


def norm(s) -> str:
    """比較用の正規化: NFKC、空白・改行除去、丸記号の揺れ（◯〇→○）を吸収。"""
    if s is None:
        return ""
    s = unicodedata.normalize("NFKC", str(s))
    s = s.replace("◯", "○").replace("〇", "○")
    return re.sub(r"\s+", "", s)


def col_key(c) -> str:
    """必須列の列名の比較キー。障害の様式種別番号（4桁）があればそれ、なければ最下段の見出し。"""
    c = unicodedata.normalize("NFKC", str(c or ""))
    m = re.search(r"(?<!\d)\d{4}(?!\d)", c)
    return m.group(0) if m else norm(c.split(">")[-1])


def required_by_compare(x: dict, y: dict) -> tuple[str, str]:
    """必須（列別）の比較用文字列。列数が同じなら位置で、違えば列名キーで対応づける（空欄省略に対応）。"""
    rx, ry = x.get("required_by") or [], y.get("required_by") or []
    if len(rx) == len(ry):
        return (" ".join(norm(r.get("value")) or "-" for r in rx), " ".join(norm(r.get("value")) or "-" for r in ry))
    f = lambda rb: " ".join(sorted(f"{col_key(r.get('column'))}={norm(r.get('value'))}" for r in rb if norm(r.get("value"))))
    return f(rx), f(ry)


def item_view(it: dict) -> dict:
    rb = it.get("required_by") or []
    return {
        "name": " > ".join(it.get("name_path") or []),
        "type": it.get("type"),
        "length": it.get("length"),
        "content": it.get("content"),
        "required": it.get("required"),
        # 値は列の位置で比べる（列見出しの読み取りは表単位の columns で別途比べる）
        "required_by": " ".join(r.get("value") or "-" for r in rb) if rb else None,
        "note": it.get("note"),
    }


def page_text(doc_id: str, domain: str, page: int, cache: dict) -> str:
    k = (doc_id, page)
    if k not in cache:
        with pymupdf.open(ROOT / "sources" / "raw" / domain / f"{doc_id}.pdf") as d:
            cache[k] = norm(d[page - 1].get_text())
    return cache[k]


def page_cells(doc_id: str, domain: str, page: int, cache: dict) -> set[str]:
    """テキストレイヤの行（≒セル）を正規化し、連続する1〜4行の連結も含めた集合。"""
    k = ("cells", doc_id, page)
    if k not in cache:
        with pymupdf.open(ROOT / "sources" / "raw" / domain / f"{doc_id}.pdf") as d:
            L = [norm(x) for x in d[page - 1].get_text().splitlines() if norm(x)]
        # 介護の PDF は「10日数・回数」のように項番と項目名が同じ行に入ることがあるので、先頭の数字を外した版も作る
        variants = [L, [re.sub(r"(数字|英数|漢字|数値|コード値)$", "", re.sub(r"^\d+", "", x)) or x for x in L]]
        cells = set()
        for V in variants:
            for i in range(len(V)):
                for w in range(1, 5):
                    cells.add("".join(V[i:i + w]))
        # 縦書き（1〜2文字ずつの行が続く）はひと続きにつなげる
        run = []
        for x in L + [""]:
            if 0 < len(x) <= 2:
                run.append(x)
            else:
                if len(run) >= 3:
                    joined = "".join(run)
                    cells.update(joined[i:j] for i in range(len(joined)) for j in range(i + 2, len(joined) + 1))
                run = []
        cache[k] = cells
    return cache[k]


def text_found(value, ptext: str) -> bool | None:
    """値がページのテキストレイヤに含まれるか。行ごとに分けて全行が見つかれば True。"""
    if value is None or norm(value) == "":
        return None
    segs = [norm(x) for x in re.split(r"[\n]| > ", str(value))]
    segs = [x for x in segs if len(x) >= 2]
    if not segs:
        return None
    return all(x in ptext for x in segs)


def check_result(res: dict, ptext: str, cells: set[str] | None = None) -> tuple[list[dict], dict]:
    issues: list[dict] = []
    stats = {"tables": 0, "items": 0, "text_checked": 0, "text_missing": 0}

    def add(level, msg, t=None, no=None, field=None, row=None):
        issues.append({"level": level, "table": t, "no": no, "field": field, "row": row, "msg": msg})

    tables = res.get("tables") or []
    stats["tables"] = len(tables)
    if not tables:
        add("warn", "表が1つも書き起こされていない")
    for ti, t in enumerate(tables):
        items = t.get("items") or []
        stats["items"] += len(items)
        kind = t.get("table_kind")
        # 1. 連番
        nos = [it.get("no") for it in items]
        seq = [n for n in nos if n is not None]
        if any(n is None for n in nos) and kind != "other":
            add("warn", f"項番が整数でない行が {sum(n is None for n in nos)} 行", ti)
        if seq:
            if not t.get("continued_from_prev_page") and seq[0] != 1:
                add("error", f"前ページからの続きではないのに項番が {seq[0]} から始まる", ti)
            for a, b in zip(seq, seq[1:]):
                if b == a:
                    continue  # 結合行（同一項番の小項目）
                if b != a + 1:
                    add("error", f"項番が連続していない: {a} → {b}", ti, b)
        # 必須（列別）の列数が行ごとにそろっているか（空欄の列を省略していないか）
        widths = [len(it.get("required_by") or []) for it in items]
        if widths and max(widths) > 0 and min(widths) != max(widths):
            short = sum(w < max(widths) for w in widths)
            add("warn", f"必須（列別）の列数が行によって違う（{short} 行が {max(widths)} 列未満）。空欄の列を省略した可能性", ti)
        # 2〜4
        for ri, it in enumerate(items):
            no = it.get("no")
            if kind in ("record_layout", "code_list"):
                L = it.get("length")
                if L is None:
                    add("warn", f"桁数が空（原文: {it.get('length_raw')!r}）", ti, no, "length", ri)
                elif not isinstance(L, int) or isinstance(L, bool):
                    add("error", f"桁数が整数でない: {L!r}", ti, no, "length", ri)
                elif L <= 0 or L > 9999:
                    add("error", f"桁数が範囲外: {L}", ti, no, "length", ri)
                ty = it.get("type")
                if ty and norm(ty) not in {norm(x) for x in KNOWN_TYPES}:
                    add("warn", f"未知の属性: {ty!r}", ti, no, "type", ri)
            r = it.get("required")
            if r is not None and norm(r) not in {norm(x) for x in REQUIRED_MARKS}:
                add("error", f"必須の値が想定外: {r!r}", ti, no, "required", ri)
            for rb in it.get("required_by") or []:
                v = rb.get("value")
                if v is not None and norm(v) not in {norm(x) for x in REQUIRED_MARKS}:
                    add("error", f"必須（{rb.get('column')}）の値が想定外: {v!r}", ti, no, "required_by", ri)
            # 5. テキストレイヤ照合
            v = item_view(it)
            # 5b. 項目名（最下段）がセルとして完全一致するか。部分一致しかしない＝文字の脱落・付け足しの疑い
            leaf = norm((it.get("name_path") or [""])[-1])
            if cells is not None and kind != "other" and len(leaf) >= 2 and leaf in ptext and leaf not in cells:
                stats["name_partial"] = stats.get("name_partial", 0) + 1
                add("warn", f"項目名がPDFのセルと完全一致しない（部分一致のみ）: {(it.get('name_path') or [''])[-1]!r}", ti, no, "name", ri)
            for f in TEXT_FIELDS:
                ok = text_found(v[f], ptext)
                if ok is None:
                    continue
                stats["text_checked"] += 1
                if not ok:
                    stats["text_missing"] += 1
                    add("text", "PDFのテキストレイヤに見つからない", ti, no, f, ri)
    return issues, stats


def align(a_items: list[dict], b_items: list[dict]) -> list[tuple[int | None, int | None]]:
    """(項番, 同一項番内の出現順) で行を対応づけ、各モデルの行インデックスの組を返す。"""
    def keyed(items):
        cnt = defaultdict(int)
        out = {}
        order = []
        for i, it in enumerate(items):
            no = it.get("no")
            k = (no, cnt[no]) if no is not None else ("idx", i)
            cnt[no] += 1
            out[k] = i
            order.append(k)
        return out, order

    ka, oa = keyed(a_items)
    kb, ob = keyed(b_items)
    keys = list(dict.fromkeys(oa + ob))
    return [(ka.get(k), kb.get(k)) for k in keys]


def diff_models(ra: dict, rb: dict) -> list[dict]:
    """2モデルの結果を表ごと・行ごと・列ごとに比較し、食い違いを返す。"""
    diffs = []
    ta, tb = ra.get("tables") or [], rb.get("tables") or []
    if len(ta) != len(tb):
        diffs.append({"table": None, "no": None, "field": "tables", "a": len(ta), "b": len(tb)})
    for ti in range(max(len(ta), len(tb))):
        A = ta[ti] if ti < len(ta) else {}
        B = tb[ti] if ti < len(tb) else {}
        for f in ("table_kind", "continued_from_prev_page", "continues_to_next_page"):
            if A.get(f) != B.get(f):
                diffs.append({"table": ti, "no": None, "field": f, "a": A.get(f), "b": B.get(f)})
        ca = [col_key(c) for c in A.get("columns") or []]
        cb = [col_key(c) for c in B.get("columns") or []]
        if ca != cb:
            diffs.append({"table": ti, "no": None, "field": "columns",
                          "a": " | ".join(A.get("columns") or []), "b": " | ".join(B.get("columns") or [])})
        ia_items, ib_items = A.get("items") or [], B.get("items") or []
        for ia, ib in align(ia_items, ib_items):
            x = ia_items[ia] if ia is not None else None
            y = ib_items[ib] if ib is not None else None
            no = (x or y).get("no")
            if x is None or y is None:
                diffs.append({"table": ti, "no": no, "field": "row", "ia": ia, "ib": ib,
                              "a": item_view(x)["name"] if x else None, "b": item_view(y)["name"] if y else None})
                continue
            vx, vy = item_view(x), item_view(y)
            for f in COMPARE_FIELDS:
                nx, ny = norm(vx[f]), norm(vy[f])
                if f == "required_by":
                    nx, ny = required_by_compare(x, y)
                if f == "name":  # 階層の区切り方の揺れは無視し、文字列として比べる
                    nx, ny = nx.replace(">", ""), ny.replace(">", "")
                if nx != ny:
                    diffs.append({"table": ti, "no": no, "field": f, "ia": ia, "ib": ib, "a": vx[f], "b": vy[f]})
    return diffs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="anthropic-png")
    args = ap.parse_args()
    run_dir = ROOT / "out" / args.run
    if not run_dir.exists():
        print(f"{run_dir} がない。先に transcribe.py を実行する", file=sys.stderr)
        return 1
    models = sorted(p.name for p in run_dir.iterdir() if p.is_dir())
    # 対象ページ: 出力ファイルから見つけ、config/pages.yaml にある分類・メモを付ける
    known = {(x["doc_id"], x["page"]): x for x in yaml.safe_load((ROOT / "config" / "pages.yaml").read_text(encoding="utf-8"))}
    found = set()
    for m in models:
        for f in (run_dir / m).glob("*_p*.json"):
            mm = re.fullmatch(r"(.+)_p(\d+)\.json", f.name)
            if mm:
                found.add((mm.group(1), int(mm.group(2))))
    profiles: dict[str, list[dict]] = {}
    pages = []
    for doc, page in sorted(found):
        x = dict(known.get((doc, page), {"doc_id": doc, "page": page, "category": []}))
        if "pair" not in x:  # 改ページの相手はテキストレイヤ判定（pagemeta）から決める
            if doc not in profiles:
                dom = "kaigo" if doc.startswith("kaigo") else "shogai"
                profiles[doc] = doc_profile(ROOT / "sources" / "raw" / dom / f"{doc}.pdf")
            prof = profiles[doc]
            if prof[page - 1]["continues_to_next"]:
                nxt = next((q["page"] for q in prof[page:] if not q["blank"]), None)
                if nxt and (doc, nxt) in found:
                    x["pair"] = nxt
        pages.append(x)
    cache: dict = {}
    report: dict = {"run": args.run, "models": models, "pages": []}

    loaded: dict[tuple[str, str, int], dict] = {}
    for p in pages:
        key = f"{p['doc_id']}_p{p['page']}"
        entry = {"key": key, **p, "by_model": {}, "diffs": None}
        for m in models:
            f = run_dir / m / f"{key}.json"
            if not f.exists():
                continue
            data = json.loads(f.read_text(encoding="utf-8"))
            res = data.get("result")
            if res is None:
                entry["by_model"][m] = {"meta": data["meta"], "issues": [{"level": "error", "msg": "JSON として解釈できない出力"}], "stats": {}}
                continue
            loaded[(m, p["doc_id"], p["page"])] = res
            ptext = page_text(p["doc_id"], res["domain"], p["page"], cache)
            issues, stats = check_result(res, ptext, page_cells(p["doc_id"], res["domain"], p["page"], cache))
            entry["by_model"][m] = {"meta": data["meta"], "issues": issues, "stats": stats}
        if len(models) >= 2 and all((m, p["doc_id"], p["page"]) in loaded for m in models[:2]):
            entry["diffs"] = diff_models(loaded[(models[0], p["doc_id"], p["page"])],
                                         loaded[(models[1], p["doc_id"], p["page"])])
        report["pages"].append(entry)

    # 6. 改ページ連続性
    for p in report["pages"]:
        pair = p.get("pair")
        if not pair or pair < p["page"]:
            continue
        for m in models:
            a = loaded.get((m, p["doc_id"], p["page"]))
            b = loaded.get((m, p["doc_id"], pair))
            if not a or not b or not a.get("tables") or not b.get("tables"):
                continue
            last_t, first_t = a["tables"][-1], b["tables"][0]
            msgs = []
            if not last_t.get("continues_to_next_page"):
                msgs.append(f"p{p['page']} の最後の表が continues_to_next_page=false")
            if not first_t.get("continued_from_prev_page"):
                msgs.append(f"p{pair} の最初の表が continued_from_prev_page=false")
            la = [it.get("no") for it in last_t.get("items") or [] if it.get("no") is not None]
            fb = [it.get("no") for it in first_t.get("items") or [] if it.get("no") is not None]
            if la and fb and fb[0] not in (la[-1], la[-1] + 1):
                msgs.append(f"項番が p{p['page']} 末尾 {la[-1]} → p{pair} 先頭 {fb[0]} で途切れる")
            if [norm(c) for c in last_t.get("columns") or []] != [norm(c) for c in first_t.get("columns") or []]:
                msgs.append("前後ページで列見出しの書き起こしが一致しない")
            for msg in msgs:
                p["by_model"][m]["issues"].append({"level": "error", "table": "pair", "no": None, "field": None, "msg": "[改ページ] " + msg})
            if not msgs:
                p["by_model"][m]["issues"].append({"level": "ok", "table": "pair", "no": None, "field": None, "msg": f"[改ページ] p{p['page']}→p{pair} の連続性 OK"})

    out = run_dir / "validation.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    # サマリ表示
    for p in report["pages"]:
        line = [f"{p['key']:32s}"]
        for m in models:
            v = p["by_model"].get(m)
            if not v:
                line.append(f"{m}: -")
                continue
            lv = defaultdict(int)
            for i in v["issues"]:
                lv[i["level"]] += 1
            s = v["stats"]
            line.append(f"{m.split('-')[1]}: items={s.get('items')} err={lv['error']} warn={lv['warn']} "
                        f"text_miss={s.get('text_missing')}/{s.get('text_checked')}")
        if p["diffs"] is not None:
            line.append(f"diffs={len(p['diffs'])}")
        print(" | ".join(line))
    print(f"\n→ {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
