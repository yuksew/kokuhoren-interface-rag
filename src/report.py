"""比較用 HTML（reports/compare.html）とコスト集計（reports/cost.md）を作る。

usage: uv run python src/report.py [--run anthropic-png]
前提: transcribe.py → validate.py を実行済み。
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pricing import PRICES, cost_usd  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FIELDS = [("no_raw", "項番"), ("name", "項目名"), ("type", "属性"), ("length", "桁数"),
          ("content", "内容"), ("required", "必須"), ("note", "備考"), ("cells", "その他の列")]
CAT_LABEL = {"simple": "単純", "merged": "セル結合", "split": "改ページ分断", "matrix": "必須対応表"}

CSS = """
body{font-family:"Hiragino Sans","Yu Gothic UI","Meiryo",sans-serif;margin:0;font-size:13px;color:#222}
header{padding:12px 20px;background:#1f3a5f;color:#fff}
header h1{margin:0;font-size:18px}
.wrap{padding:12px 20px}
table{border-collapse:collapse}
.summary td,.summary th{border:1px solid #bbb;padding:3px 6px;text-align:right}
.summary th{background:#eef}
.summary td.l{text-align:left}
section.page{border-top:3px solid #1f3a5f;margin-top:28px;padding-top:8px}
.grid{display:grid;grid-template-columns:minmax(380px,40%) 1fr;gap:14px;align-items:start}
.img{position:sticky;top:6px;max-height:96vh;overflow:auto;border:1px solid #ccc}
.img img{width:100%;display:block;cursor:zoom-in}
.img img.zoom{width:200%;cursor:zoom-out}
.models{display:grid;grid-template-columns:1fr;gap:12px}
.model h3{margin:4px 0;font-size:14px}
.items td,.items th{border:1px solid #ccc;padding:2px 4px;vertical-align:top;white-space:pre-wrap;word-break:break-all}
.items th{background:#f2f2f2;position:sticky;top:0}
td.diff{background:#fff2a8}
td.miss{outline:2px solid #e33;outline-offset:-2px}
td.chk{background:#ffd6d6}
tr.onlyone td{background:#ffe0b3}
.issues{margin:4px 0;padding-left:18px}
.issues li.error{color:#b00}
.issues li.warn{color:#a60}
.issues li.ok{color:#070}
.issues li.text{color:#555}
.badge{display:inline-block;padding:0 6px;border-radius:8px;background:#ddd;margin-right:4px;font-size:11px}
.legend span{display:inline-block;padding:1px 6px;margin-right:8px;border:1px solid #ccc}
.meta{color:#666;font-size:11px}
details{margin:4px 0}
.hide-same tr.same{display:none}
"""

JS = """
document.querySelectorAll('.img img').forEach(i=>i.addEventListener('click',()=>i.classList.toggle('zoom')));
document.getElementById('onlydiff').addEventListener('change',e=>document.body.classList.toggle('hide-same',e.target.checked));
"""


def esc(v) -> str:
    return "" if v is None else html.escape(str(v))


def item_cells(it: dict) -> dict:
    rb = it.get("required_by") or []
    req = it.get("required")
    if rb:
        req = " ".join(f"{r.get('column')}:{r.get('value') or '－'}" for r in rb)
    return {
        "no_raw": it.get("no_raw") if it.get("no_raw") is not None else it.get("no"),
        "name": " > ".join(it.get("name_path") or []),
        "type": it.get("type"),
        "length": it.get("length") if it.get("length") is not None else it.get("length_raw"),
        "content": it.get("content"),
        "required": req,
        "note": it.get("note"),
        "cells": "\n".join(f"{c.get('column')}: {c.get('value') if c.get('value') is not None else '－'}" for c in it.get("cells") or []) or None,
    }


def render_model(model: str, res: dict | None, v: dict, other: str | None, diffs: list[dict] | None, side: str) -> str:
    out = [f'<div class="model"><h3>{esc(model)}</h3>']
    meta = v.get("meta", {})
    u = meta.get("usage", {})
    out.append(f'<div class="meta">in={u.get("input_tokens")} out={u.get("output_tokens")} '
               f'${meta.get("cost_usd")} stop={esc(meta.get("stop_reason"))} {meta.get("latency_s")}s</div>')
    iss = v.get("issues", [])
    shown = [i for i in iss if i["level"] in ("error", "warn", "ok")]
    ntext = sum(1 for i in iss if i["level"] == "text")
    if shown or ntext:
        out.append('<ul class="issues">')
        for i in shown:
            loc = "" if i.get("table") in (None, "pair") else f"表{i['table'] + 1} "
            loc += "" if i.get("no") is None else f"項番{i['no']} "
            out.append(f'<li class="{i["level"]}">{esc(loc)}{esc(i["msg"])}</li>')
        if ntext:
            out.append(f'<li class="text">テキストレイヤに見つからないセル: {ntext} 個（赤枠）</li>')
        out.append("</ul>")
    if res is None:
        out.append("<p>（出力なし）</p></div>")
        return "".join(out)

    diff_cells: dict[tuple[int, int], dict[str, dict]] = defaultdict(dict)
    only_rows: set[tuple[int, int]] = set()
    idx_key = "ia" if side == "a" else "ib"
    for d in diffs or []:
        if d.get("table") is None or d.get(idx_key) is None:
            continue
        if d["field"] == "row":
            only_rows.add((d["table"], d[idx_key]))
        elif d["field"] in ("name", "type", "length", "content", "required", "required_by", "note", "cells"):
            f = "required" if d["field"] == "required_by" else d["field"]
            diff_cells[(d["table"], d[idx_key])][f] = d["b" if side == "a" else "a"]
    miss = {(i["table"], i.get("row"), i["field"]) for i in iss if i["level"] == "text"}
    chk = {(i["table"], i.get("row"), "required" if i["field"] == "required_by" else i["field"])
           for i in iss if i["level"] in ("error", "warn") and i.get("row") is not None}

    for ti, t in enumerate(res.get("tables") or []):
        flags = []
        if t.get("continued_from_prev_page"):
            flags.append("前頁から続く")
        if t.get("continues_to_next_page"):
            flags.append("次頁へ続く")
        rec = t.get("record") or {}
        out.append(f'<details open><summary><b>表{ti + 1}</b> <span class="badge">{esc(t.get("table_kind"))}</span>'
                   f'{esc(t.get("title"))} {"".join(f"<span class=badge>{f}</span>" for f in flags)}'
                   f' <span class="meta">record={esc(rec.get("name"))} parent={esc(rec.get("parent"))} '
                   f'id={esc(rec.get("exchange_id"))}</span></summary>')
        out.append(f'<div class="meta">列: {esc(" | ".join(t.get("columns") or []))}</div>')
        cm = {k: v for k, v in (t.get("column_map") or {}).items() if v}
        if cm:
            out.append(f'<div class="meta">列の対応: {esc(", ".join(f"{k}={v}" for k, v in cm.items()))}</div>')
        out.append('<table class="items"><tr>' + "".join(f"<th>{lbl}</th>" for _, lbl in FIELDS) + "</tr>")
        for ri, it in enumerate(t.get("items") or []):
            c = item_cells(it)
            dc = diff_cells.get((ti, ri), {})
            cls = "onlyone" if (ti, ri) in only_rows else ("diff" if dc else "same")
            out.append(f'<tr class="{cls}">')
            for f, _ in FIELDS:
                tdc = []
                title = ""
                if f in dc:
                    tdc.append("diff")
                    title = f"{other}: {dc[f]}"
                if (ti, ri, f) in miss:
                    tdc.append("miss")
                    title += (" / " if title else "") + "PDFテキストに見つからない"
                if (ti, ri, f) in chk:
                    tdc.append("chk")
                out.append(f'<td class="{" ".join(tdc)}" title="{esc(title)}">{esc(c[f])}</td>')
            out.append("</tr>")
        out.append("</table></details>")
    if res.get("footnotes"):
        out.append("<details><summary>注記</summary><ul>" + "".join(
            f"<li>{esc(fn.get('mark'))} {esc(fn.get('text'))}</li>" for fn in res["footnotes"]) + "</ul></details>")
    if res.get("uncertain"):
        out.append("<details open><summary>uncertain（モデル自己申告）</summary><ul>" + "".join(
            f"<li>{esc(x)}</li>" for x in res["uncertain"]) + "</ul></details>")
    out.append("</div>")
    return "".join(out)


def page_score(p: dict) -> int:
    """要確認度: エラー・警告・テキスト不一致・モデル間の食い違いの数。"""
    n = len([d for d in (p.get("diffs") or []) if d["field"] != "tables"])
    for v in p["by_model"].values():
        n += sum(1 for i in v.get("issues", []) if i["level"] in ("error", "warn", "text"))
    return n


def ensure_img(key: str, doc: str, page: int) -> None:
    f = ROOT / "reports" / "img" / f"{key}.png"
    if f.exists():
        return
    import pymupdf

    dom = "kaigo" if doc.startswith("kaigo") else "shogai"
    f.parent.mkdir(parents=True, exist_ok=True)
    with pymupdf.open(ROOT / "sources" / "raw" / dom / f"{doc}.pdf") as d:
        d[page - 1].get_pixmap(dpi=110).save(str(f))


def aggregate_table(val: dict) -> str:
    models = val["models"]
    agg: dict = defaultdict(lambda: defaultdict(int))
    for p in val["pages"]:
        a = agg[p["doc_id"]]
        a["pages"] += 1
        nd = len([d for d in (p.get("diffs") or []) if d["field"] not in ("tables",)])
        a["diff_cells"] += nd
        a["pages_with_diff"] += nd > 0
        a["pages_flagged"] += page_score(p) > 0
        for m in models:
            v = p["by_model"].get(m) or {}
            s = v.get("stats", {})
            a[f"{m}:items"] += s.get("items", 0) or 0
            a[f"{m}:err"] += sum(1 for i in v.get("issues", []) if i["level"] == "error")
            a[f"{m}:warn"] += sum(1 for i in v.get("issues", []) if i["level"] == "warn")
            a[f"{m}:text"] += s.get("text_missing", 0) or 0
            a[f"{m}:cost"] += (v.get("meta") or {}).get("cost_usd_batch" if (v.get("meta") or {}).get("billed_as") == "batch" else "cost_usd", 0) or 0
    h = ['<h2>文書別の集計</h2><table class="summary"><tr><th>文書</th><th>ページ</th><th>食い違いのあるページ</th><th>食い違いセル</th><th>要確認ページ</th>']
    for m in models:
        h.append(f"<th colspan=5>{esc(m)}</th>")
    h.append("</tr><tr><th></th><th></th><th></th><th></th><th></th>" + "<th>行数</th><th>error</th><th>warn</th><th>テキスト不一致</th><th>$（実費）</th>" * len(models) + "</tr>")
    for doc, a in agg.items():
        h.append(f"<tr><td class=l>{esc(doc)}</td><td>{a['pages']}</td><td>{a['pages_with_diff']}</td><td>{a['diff_cells']}</td><td>{a['pages_flagged']}</td>")
        for m in models:
            h.append(f"<td>{a[m + ':items']}</td><td>{a[m + ':err']}</td><td>{a[m + ':warn']}</td><td>{a[m + ':text']}</td><td>{a[m + ':cost']:.3f}</td>")
        h.append("</tr>")
    h.append("</table>")
    return "".join(h)


def build_html(run: str, val: dict) -> str:
    run_dir = ROOT / "out" / run
    models = val["models"]
    parts = [f"<!DOCTYPE html><html lang=ja><head><meta charset=utf-8><title>書き起こし比較 {esc(run)}</title>"
             f"<style>{CSS}</style></head><body>"
             f"<header><h1>インタフェース仕様書 書き起こし比較（{esc(run)}）</h1></header><div class=wrap>"]
    parts.append('<p class="legend"><span style="background:#fff2a8">モデル間で食い違い（マウスオーバーで相手の値）</span>'
                 '<span style="outline:2px solid #e33">PDFテキストレイヤに見つからない</span>'
                 '<span style="background:#ffd6d6">自動チェックで警告・エラー</span>'
                 '<span style="background:#ffe0b3">片方のモデルにしかない行</span>'
                 ' <label><input type=checkbox id=onlydiff> 食い違いのある行だけ表示</label></p>')
    # サマリ
    big = len(val["pages"]) > 30
    shown = [p for p in val["pages"] if not big or page_score(p) > 0]
    if big:
        parts.append(aggregate_table(val))
        parts.append(f"<p>全 {len(val['pages'])} ページのうち、要確認（エラー・警告・テキスト不一致・食い違いのいずれかがある）{len(shown)} ページだけを以下に表示する。</p>")
    parts.append('<table class="summary"><tr><th>ページ</th><th>種類</th>')
    for m in models:
        parts.append(f'<th colspan=5>{esc(m)}</th>')
    parts.append("<th>食い違い</th></tr><tr><th></th><th></th>")
    for _ in models:
        parts.append("<th>行数</th><th>error</th><th>warn</th><th>テキスト不一致</th><th>$</th>")
    parts.append("<th>セル</th></tr>")
    for p in shown:
        cat = "・".join(CAT_LABEL.get(c, c) for c in p.get("category", []))
        parts.append(f'<tr><td class=l><a href="#{p["key"]}">{esc(p["key"])}</a> (印字p.{esc(p.get("printed"))})</td><td class=l>{cat}</td>')
        for m in models:
            v = p["by_model"].get(m)
            if not v:
                parts.append("<td colspan=5>-</td>")
                continue
            lv = defaultdict(int)
            for i in v["issues"]:
                lv[i["level"]] += 1
            s = v.get("stats", {})
            parts.append(f"<td>{s.get('items', '-')}</td><td>{lv['error']}</td><td>{lv['warn']}</td>"
                         f"<td>{s.get('text_missing', '-')}/{s.get('text_checked', '-')}</td>"
                         f"<td>{v['meta'].get('cost_usd')}</td>")
        parts.append(f"<td>{'-' if p['diffs'] is None else len([d for d in p['diffs'] if d['field'] != 'tables'])}</td></tr>")
    parts.append("</table>")

    for p in shown:
        ensure_img(p["key"], p["doc_id"], p["page"])
        parts.append(f'<section class="page" id="{p["key"]}"><h2>{esc(p["key"])} — 印字p.{esc(p.get("printed"))} '
                     f'<span class=meta>{esc(p.get("note"))}</span></h2><div class="grid">')
        parts.append(f'<div class="img"><img src="img/{p["key"]}.png" alt="{esc(p["key"])}"></div><div class="models">')
        for side, m in zip("ab", models):
            f = run_dir / m / f"{p['key']}.json"
            res = json.loads(f.read_text(encoding="utf-8"))["result"] if f.exists() else None
            other = models[1] if side == "a" and len(models) > 1 else (models[0] if side == "b" else None)
            parts.append(render_model(m, res, p["by_model"].get(m, {}), other, p.get("diffs"), side))
        parts.append("</div></div></section>")
    parts.append(f"</div><script>{JS}</script></body></html>")
    return "".join(parts)


def count_pages(domains_volumes: list[str]) -> dict[str, int]:
    log = json.loads((ROOT / "sources" / "fetch_log.json").read_text(encoding="utf-8"))
    return {k: v["pages"] for k, v in log.items() if k in domains_volumes}


def build_cost(run: str) -> str:
    import yaml

    calls = [json.loads(x) for x in (ROOT / "out" / run / "calls.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    # 同じページを再実行した場合は最新のみ
    latest = {}
    for c in calls:
        latest[(c["requested_model"], c["doc_id"], c["page"])] = c
    calls = list(latest.values())
    by_model = defaultdict(list)
    for c in calls:
        by_model[c["requested_model"]].append(c)

    manifest = yaml.safe_load((ROOT / "sources" / "manifest.yaml").read_text(encoding="utf-8"))
    log = json.loads((ROOT / "sources" / "fetch_log.json").read_text(encoding="utf-8"))
    spec_pages = defaultdict(int)
    for e in manifest:
        if e["kind"] == "spec":
            spec_pages[e["domain"]] += log[e["id"]]["pages"] or 0
    jig_pages = {k: log[k]["pages"] for k in ("kaigo_kyotsu_r0806", "kaigo_jigyosho_r0604", "kaigo_kyotaku_r0604",
                                                "shogai_kyotsu_r0710", "shogai_jigyosho_r0710")}

    L = [f"# 書き起こしコスト（run: {run}）", "",
         "単価（USD / 100万トークン）: " + ", ".join(f"{m} 入力${p['input']} 出力${p['output']}" for m, p in PRICES.items())
         + "。Batch API は 50% 引き。", "",
         "## 呼び出しごと", "",
         "| モデル | ページ | 種類 | 入力tok | 出力tok | 秒 | 通常$ | Batch$ | stop |",
         "|---|---|---|--:|--:|--:|--:|--:|---|"]
    for c in sorted(calls, key=lambda c: (c["requested_model"], c["doc_id"], c["page"])):
        u = c["usage"]
        L.append(f"| {c['requested_model']} | {c['doc_id']} p{c['page']} | {'・'.join(c.get('category', []))} | "
                 f"{u['input_tokens']:,} | {u['output_tokens']:,} | {c['latency_s']} | {c['cost_usd']:.4f} | "
                 f"{c['cost_usd_batch']:.4f} | {c['stop_reason']} |")
    L += ["", "## モデル別 合計・1ページ平均", "",
          "| モデル | ページ数 | 入力tok計 | 出力tok計 | 通常$計 | Batch$計 | 平均入力tok/頁 | 平均出力tok/頁 | 通常$/頁 | Batch$/頁 |",
          "|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|"]
    grand = 0.0
    avg = {}
    for m, cs in sorted(by_model.items()):
        it = sum(c["usage"]["input_tokens"] for c in cs)
        ot = sum(c["usage"]["output_tokens"] for c in cs)
        cu = sum(c["cost_usd"] for c in cs)
        cb = sum(c["cost_usd_batch"] for c in cs)
        grand += cu
        ai, ao = mean(c["usage"]["input_tokens"] for c in cs), mean(c["usage"]["output_tokens"] for c in cs)
        avg[m] = (ai, ao)
        L.append(f"| {m} | {len(cs)} | {it:,} | {ot:,} | {cu:.4f} | {cb:.4f} | {ai:,.0f} | {ao:,.0f} | "
                 f"{cu / len(cs):.4f} | {cb / len(cs):.4f} |")
    L += ["", f"**この検証の合計（通常 API）: ${grand:.4f}**", ""]

    L += ["## 全ページ処理した場合の見積もり", "",
          "検証ページの平均トークン数 × ページ数で単純計算した値。表のないページ（目次・図・空白ページ）も含めて数えているので上振れ側の見積もり。"
          "検証ページは表が詰まったページを選んでいるため、1ページあたりの出力トークンも実際より多めに出ている可能性が高い。", ""]
    scopes = [("事業所向け（介護: 共通編＋サービス事業所編＋居宅介護支援事業所編 / 障害: 共通編＋事業所編）", sum(jig_pages.values())),
              ("介護 manifest の spec 全部", spec_pages["kaigo"]),
              ("障害 manifest の spec 全部", spec_pages["shogai"]),
              ("両分野 spec 全部", spec_pages["kaigo"] + spec_pages["shogai"])]
    L += ["| 範囲 | ページ数 | " + " | ".join(f"{m} 通常$ | {m} Batch$" for m in avg) + " |",
          "|---|--:|" + "--:|--:|" * len(avg)]
    for name, n in scopes:
        row = f"| {name} | {n:,} |"
        for m, (ai, ao) in avg.items():
            row += f" {cost_usd(m, int(ai), int(ao)) * n:,.2f} | {cost_usd(m, int(ai), int(ao), batch=True) * n:,.2f} |"
        L.append(row)
    L += ["", "対象ページ数の内訳: " + ", ".join(f"{k}={v}" for k, v in jig_pages.items()), ""]
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="anthropic-png")
    args = ap.parse_args()
    val = json.loads((ROOT / "out" / args.run / "validation.json").read_text(encoding="utf-8"))
    rep = ROOT / "reports"
    rep.mkdir(exist_ok=True)
    suffix = "" if args.run == "anthropic-png" else f".{args.run}"
    (rep / f"compare{suffix}.html").write_text(build_html(args.run, val), encoding="utf-8")
    (rep / f"cost{suffix}.md").write_text(build_cost(args.run), encoding="utf-8")
    print(f"→ reports/compare{suffix}.html, reports/cost{suffix}.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
