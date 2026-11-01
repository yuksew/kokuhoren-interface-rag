"""2モデルの書き起こしから採用版を作り、人が確認すべき箇所を一覧にする。

採用ルール（reports/pilot_report.md の結論）
  1. 基本は Haiku の結果を採用する。
  2. 片方が省略（行0・uncertain に省略の記載）していれば、もう片方を採用する。
  3. 必須対応表（required_matrix）は Haiku を採用する（Sonnet は大きな表を打ち切るため）。
  4. Haiku の表に「原本の文字に無い列名」があり、Sonnet の同じ位置の表に無ければ、その表は Sonnet を採用する。
  5. セル単位で食い違う場合は PDF テキストレイヤで判定する:
     - Sonnet の値だけがテキストレイヤと一致 → Sonnet の値に置き換える（自動修正）
     - それ以外（両方一致・両方不一致・照合できない列） → Haiku のまま、確認キューに入れる

usage: uv run python src/adopt.py [--run prod1-png-post]
  前提: postprocess.py と validate.py を実行済み
出力:
  out/{run}-adopted/{doc_id}_p{page}.json   採用版（表ごとに source_model、自動修正は _fixes に記録）
  out/{run}-adopted/logical_tables.json     ページをまたぐ表を結合した論理的な表
  reports/review_queue.{run}.csv            確認キュー（Excel で開けるよう UTF-8 BOM 付き）
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pagemeta import doc_profile  # noqa: E402
from postprocess import build_logical  # noqa: E402
from validate import diff_models, item_view, norm, page_cells, page_text, text_found  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PRIMARY, SECOND = "claude-haiku-5-5", "claude-sonnet-5-5"
ARBITRABLE = {"name", "content", "note", "cells"}


def text_ok(field: str, value, ptext: str, cells: set[str]) -> bool | None:
    if value is None or norm(value) == "":
        return None
    if field == "name":
        return norm(str(value).split(" > ")[-1]) in cells
    return text_found(value, ptext)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="prod1-png-post")
    args = ap.parse_args()
    run_dir = ROOT / "out" / args.run
    out_dir = ROOT / "out" / f"{args.run}-adopted"
    out_dir.mkdir(parents=True, exist_ok=True)
    val = json.loads((run_dir / "validation.json").read_text(encoding="utf-8"))
    cache: dict = {}
    profiles: dict[str, list[dict]] = {}
    stats = Counter()
    queue = []
    pages_by_doc: dict[str, list[tuple[int, dict]]] = defaultdict(list)

    for p in val["pages"]:
        key, doc, page = p["key"], p["doc_id"], p["page"]
        dom = "kaigo" if doc.startswith("kaigo") else "shogai"
        if doc not in profiles:
            profiles[doc] = doc_profile(ROOT / "sources" / "raw" / dom / f"{doc}.pdf")
        res = {}
        for m in (PRIMARY, SECOND):
            f = run_dir / m / f"{key}.json"
            res[m] = json.loads(f.read_text(encoding="utf-8"))["result"] if f.exists() else None
        iss = {m: (p["by_model"].get(m) or {}).get("issues", []) for m in (PRIMARY, SECOND)}
        omitted = {m: res[m] is None or any(i["msg"].startswith("[省略]") for i in iss[m]) for m in (PRIMARY, SECOND)}

        # ページ単位の選択（ルール 1・2）
        if omitted[PRIMARY] and not omitted[SECOND]:
            base_m, other_m = SECOND, PRIMARY
            stats["page_from_sonnet_(haiku_omitted)"] += 1
        else:
            base_m, other_m = PRIMARY, SECOND
            if omitted[PRIMARY]:
                stats["page_both_omitted"] += 1
                queue.append([doc, page, "", "", "page", "両モデルとも省略・出力なし", "", "", "要確認"])
        adopted = copy.deepcopy(res[base_m]) if res[base_m] else {"tables": []}
        for t in adopted.get("tables") or []:
            t["source_model"] = base_m
        other = res[other_m] if not omitted[other_m] else None

        # 表単位の差し替え（ルール 4）。ルール 3: required_matrix は Haiku のまま
        invented = {i["table"] for i in iss[PRIMARY] if i["msg"].startswith("[列] 原本の文字に無い列名")}
        invented_s = {i["table"] for i in iss[SECOND] if i["msg"].startswith("[列] 原本の文字に無い列名")}
        if base_m == PRIMARY:
            for ti in sorted(invented):
                st = (other.get("tables") or []) if other else []
                if ti < len(st) and ti not in invented_s and adopted["tables"][ti].get("table_kind") != "required_matrix":
                    adopted["tables"][ti] = copy.deepcopy(st[ti])
                    adopted["tables"][ti]["source_model"] = SECOND
                    adopted["tables"][ti]["_adopt_reason"] = "Haiku の列名が原本に無いため Sonnet の表を採用"
                    stats["table_from_sonnet_(invented_columns)"] += 1
                else:
                    msg = next(i["msg"] for i in iss[PRIMARY] if i.get("table") == ti and i["msg"].startswith("[列] 原本の文字に無い列名"))
                    stats["review_invented_columns"] += 1
                    queue.append([doc, page, ti + 1, "", "columns", "列名が原本に無い（差し替え先が無いため Haiku のまま）",
                                  msg.split(": ", 1)[-1], "", "要確認"])

        # セル単位の判定（ルール 5）
        if base_m == PRIMARY and other:
            ptext = page_text(doc, dom, page, cache)
            cells = page_cells(doc, dom, page, cache)
            haiku_text = norm("".join(
                " ".join(str(x) for x in [item_view(it)["name"], it.get("content"), it.get("note")] if x)
                for t in adopted.get("tables") or [] for it in t.get("items") or []))
            for d in diff_models(adopted, other):
                ti, field = d.get("table"), d["field"]
                if ti is None or d.get("ia") is None or d.get("ib") is None:
                    if field == "row" and ti is not None:
                        # 行の切り方の違い（コード値を1行ずつに分けた等）は文字がそろっていれば問題にしない
                        if d.get("ib") is not None:  # Sonnet にだけある行
                            it = other["tables"][ti]["items"][d["ib"]]
                            row_txt = norm(" ".join(str(x) for x in [item_view(it)["name"], it.get("content")] if x))
                            if row_txt and row_txt in ptext and row_txt not in haiku_text:
                                stats["review_row_missing_in_haiku"] += 1
                                queue.append([doc, page, ti + 1, d.get("no"), "row", "Haiku に無い行（Sonnet にあり、原本にもある）",
                                              "", d.get("b"), "要確認"])
                            else:
                                stats["row_split_difference"] += 1
                        else:  # Haiku にだけある行
                            it = adopted["tables"][ti]["items"][d["ia"]]
                            checks = [text_found(x, ptext) for x in (item_view(it)["name"], it.get("content"))]
                            if any(c is False for c in checks):
                                stats["review_row_not_in_source"] += 1
                                queue.append([doc, page, ti + 1, d.get("no"), "row", "Haiku にだけある行で、原本の文字と一致しない",
                                              d.get("a"), "", "要確認"])
                            else:
                                stats["row_split_difference"] += 1
                    continue
                t = adopted["tables"][ti]
                if t.get("source_model") != PRIMARY or t.get("table_kind") == "required_matrix" and field != "name":
                    if field in ("required_by", "required"):
                        stats["matrix_diff_kept_haiku"] += 1
                        queue.append([doc, page, ti + 1, d.get("no"), field, "必須記号の食い違い（Haiku を採用）",
                                      d.get("a"), d.get("b"), "要確認"])
                    continue
                it_h = t["items"][d["ia"]]
                it_s = other["tables"][ti]["items"][d["ib"]]
                if field in ARBITRABLE:
                    vh, vs = item_view(it_h)[field], item_view(it_s)[field]
                    if field == "cells":
                        vh = "\n".join(str(c.get("value")) for c in it_h.get("cells") or [] if c.get("value")) or None
                        vs = "\n".join(str(c.get("value")) for c in it_s.get("cells") or [] if c.get("value")) or None
                    oh, os_ = text_ok(field, vh, ptext, cells), text_ok(field, vs, ptext, cells)
                    if os_ and not oh:
                        src_field = {"name": "name_path"}.get(field, field)
                        it_h.setdefault("_fixes", []).append({"field": src_field, "from": copy.deepcopy(it_h.get(src_field)),
                                                              "to": copy.deepcopy(it_s.get(src_field)), "by": "textlayer"})
                        it_h[src_field] = copy.deepcopy(it_s.get(src_field))
                        stats[f"auto_fix_{field}"] += 1
                        continue
                    verdict = ("両方ともテキストと一致（表記の差）" if oh and os_ else
                               "Haiku のみテキストと一致" if oh and not os_ else
                               "両方ともテキストと不一致" if oh is False and os_ is False else "照合できない")
                    if oh and not os_:
                        stats["kept_haiku_textlayer"] += 1
                        continue  # Haiku が正しいと判定できたものはキューに入れない
                    if oh and os_:
                        stats["same_text_different_split"] += 1
                        continue
                else:
                    verdict = "テキストで照合できない列"
                stats[f"review_{field}"] += 1
                queue.append([doc, page, ti + 1, d.get("no"), field, verdict, d.get("a"), d.get("b"), "要確認"])

        body = {"domain": dom, "doc_id": doc, "page": page, **adopted}
        (out_dir / f"{key}.json").write_text(json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8")
        pages_by_doc[doc].append((page, adopted))
        stats["pages"] += 1

    logical, joined = build_logical(pages_by_doc, profiles)
    (out_dir / "logical_tables.json").write_text(json.dumps(logical, ensure_ascii=False, indent=1), encoding="utf-8")
    stats["logical_tables"] = len(logical)
    stats["review_total"] = len(queue)

    qf = ROOT / "reports" / f"review_queue.{args.run}.csv"
    with qf.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["文書", "PDFページ", "表", "項番", "列", "判定", "Haiku", "Sonnet", "状態"])
        w.writerows(queue)
    for k, v in sorted(stats.items()):
        print(f"{k}: {v}")
    print(f"→ {out_dir.relative_to(ROOT)}, {qf.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
