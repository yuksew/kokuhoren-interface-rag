"""確認キューを原本と見比べて判定するための画面（この PC のブラウザで使う。API は呼ばない）。

usage: uv run python src/review_app.py [--run prod1-png-post] [--port 8765] [--no-browser]
  前提: adopt.py を実行済み（reports/review_queue.{run}.json がある）
  判定はその場で reports/review_decisions.{run}.json に保存される。途中でやめても続きから再開できる。
  反映は apply_review.py で行う。
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import threading
import webbrowser
from collections import Counter, defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from review_core import (FIELD_LABEL, FIELD_LABEL_EXTRA, ROOT, apply_page, col_field, compare_cols, get_cell,  # noqa: E402
                         load_decisions, load_page, load_queue, norm, save_decisions, table_columns)

DPI = 150
IMG_DIR = ROOT / "out" / "review_img"
LOCK = threading.Lock()
DOC_LABEL = {"kaigo_kyotsu": "介護 共通編", "kaigo_jigyosho": "介護 サービス事業所編",
             "shogai_kyotsu": "障害 共通編", "shogai_jigyosho": "障害 事業所編"}


def doc_label(doc: str) -> str:
    return next((v for k, v in DOC_LABEL.items() if doc.startswith(k)), doc)


def pdf_file(doc: str) -> Path:
    dom = "kaigo" if doc.startswith("kaigo") else "shogai"
    return ROOT / "sources" / "raw" / dom / f"{doc}.pdf"


def page_image(doc: str, page: int) -> Path:
    f = IMG_DIR / f"{doc}_p{page}.png"
    if not f.exists():
        IMG_DIR.mkdir(parents=True, exist_ok=True)
        with pymupdf.open(pdf_file(doc)) as d:
            d[page - 1].get_pixmap(dpi=DPI).save(str(f))
    return f


_band_cache: dict = {}


def row_bands(doc: str, page: int, rows: list[tuple[str, str, str]]) -> dict[str, list[float]]:
    """行ごとに、原本のどこにあるか（ページ幅いっぱいの帯、0〜1 の比率）を探す。
    まず項番を表の左端の単語として探し、見つからなければ項目名で探す。同じものが複数あれば上から順に割り当てる。"""
    out = {}
    with pymupdf.open(pdf_file(doc)) as d:
        pg = d[page - 1]
        W, H = pg.rect.width, pg.rect.height
        words = pg.get_text("words")
        left: dict[str, list] = defaultdict(list)
        for w in sorted(words, key=lambda w: (w[1], w[0])):
            t = norm(w[4])
            if t.isdigit() and w[0] < W * 0.3:
                left[t].append(pymupdf.Rect(w[:4]))
        used = Counter()
        for rowkey, no, name in rows:
            hits, k = [], 0
            if no and norm(no).isdigit() and left.get(norm(no)):
                hits, key = left[norm(no)], ("no", norm(no))
            else:
                key = ("name", name)
                for cand in (name, name[:8]):
                    if cand and len(norm(cand)) >= 2:
                        hits = sorted(pg.search_for(cand), key=lambda r: (r.y0, r.x0))
                        if hits:
                            break
            if not hits:
                continue
            k = used[key]
            used[key] += 1
            r = hits[min(k, len(hits) - 1)]
            out[rowkey] = [r.x0 / W, r.y0 / H, r.x1 / W, r.y1 / H]
    return out


class App:
    def __init__(self, run: str):
        self.run = run
        self.queue = load_queue(run)
        self.by_page: dict[tuple[str, int], list[dict]] = defaultdict(list)
        for q in self.queue:
            self.by_page[(q["doc"], q["page"])].append(q)
        self.order = sorted(self.by_page, key=lambda k: (not k[0].startswith("kaigo"), "jigyosho" in k[0], k[0], k[1]))

    def pages(self) -> dict:
        dec = load_decisions(self.run)
        out = []
        for doc, page in self.order:
            qs = self.by_page[(doc, page)]
            acts = [dec["items"].get(q["id"], {}).get("action") for q in qs]
            out.append({"doc": doc, "page": page, "label": doc_label(doc), "n": len(qs),
                        "done": sum(a not in (None, "hold") for a in acts), "hold": sum(a == "hold" for a in acts),
                        "verdicts": sorted({q["verdict"] for q in qs})})
        verdicts = Counter(q["verdict"] for q in self.queue)
        return {"run": self.run, "pages": out, "verdicts": verdicts.most_common(),
                "docs": sorted({doc_label(d) for d, _ in self.order})}

    def page(self, doc: str, page: int) -> dict:
        qs = self.by_page[(doc, page)]
        dec = load_decisions(self.run)
        adopted, sonnet = load_page(self.run, doc, page)
        view = apply_page(adopted, sonnet, qs, dec, final=False)
        s_tables = (sonnet or {}).get("tables") or []
        tables, names = [], []
        for ti, t in enumerate(view.get("tables") or []):
            cols = table_columns(t)
            kinds = [col_field(t, c) for c in cols]
            rows = []
            for it in t.get("items") or []:
                rk = f"q:{it['_qid']}" if it.get("_qid") else str(it.get("_ia"))
                rows.append({"key": rk, "no": it.get("no_raw") or it.get("no"),
                             "values": [get_cell(t, it, c) for c in cols],
                             "deleted": bool(it.get("_deleted")), "added": bool(it.get("_added")), "ghost": bool(it.get("_ghost")),
                             "human": any(f.get("by") == "human" for f in it.get("_fixes") or []),
                             "auto": any(f.get("by") == "textlayer" for f in it.get("_fixes") or [])})
                nm = (it.get("name_path") or [""])[-1]
                names.append((f"{ti}:{rk}", str(it.get("no_raw") or it.get("no") or ""), nm))
            tables.append({"title": t.get("title") or "", "kind": t.get("table_kind"), "source": t.get("source_model"),
                           "columns": cols, "fixed": [k is not None for k in kinds], "fields": kinds, "rows": rows,
                           "matrix": t.get("table_kind") == "required_matrix" or sum(k is None for k in kinds) >= 5})
        items = []
        a_tables = adopted.get("tables") or []
        for q in qs:
            it = {k: q[k] for k in ("id", "field", "verdict", "detail", "haiku", "sonnet", "table", "no")}
            it["field_label"] = FIELD_LABEL.get(q["field"]) or FIELD_LABEL_EXTRA.get(q["field"], q["field"])
            it["decision"] = dec["items"].get(q["id"])
            it["row"] = (f"q:{q['id']}" if q.get("ia") is None and q.get("ib") is not None
                         else None if q.get("ia") is None else str(q["ia"]))
            diff, hv, sv = [], {}, {}
            if q.get("table") is not None and q["table"] < len(a_tables) and q.get("ia") is not None:
                ht = a_tables[q["table"]]
                hi = ht["items"][q["ia"]]
                st = s_tables[q["table"]] if q["table"] < len(s_tables) else None
                si = st["items"][q["ib"]] if st is not None and q.get("ib") is not None and q["ib"] < len(st.get("items") or []) else None
                diff, hv, sv = compare_cols(ht, hi, st, si, q["field"], table_columns(view["tables"][q["table"]]))
            it.update({"diffcols": diff, "haiku_vals": hv, "sonnet_vals": sv})
            items.append(it)
        img = page_image(doc, page)
        with pymupdf.open(pdf_file(doc)) as d:
            r = d[page - 1].rect
        return {"doc": doc, "page": page, "label": doc_label(doc), "img": f"/img/{img.name}",
                "aspect": r.height / r.width, "tables": tables, "items": items,
                "bands": row_bands(doc, page, names), "cells": {k: v for k, v in dec["cells"].items()
                                                                 if k.startswith(f"{doc}|{page}|")}}

    def decide(self, body: dict) -> dict:
        now = dt.datetime.now().isoformat(timespec="seconds")
        with LOCK:
            dec = load_decisions(self.run)
            for d in body.get("items") or []:
                if d.get("decision") is None:
                    dec["items"].pop(d["id"], None)
                else:
                    dec["items"][d["id"]] = {**d["decision"], "at": now}
            for c in body.get("cells") or []:
                if c.get("clear"):
                    dec["cells"].pop(c["key"], None)
                else:
                    dec["cells"][c["key"]] = {"value": c.get("value"), "no": c.get("no"), "at": now}
            save_decisions(self.run, dec)
        return {"ok": True}


def make_handler(app: App):
    ui_file = Path(__file__).resolve().parent / "review_ui.html"

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code: int, body: bytes, ctype: str):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, obj):
            self._send(200, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

        def do_GET(self):
            u = urlparse(self.path)
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            try:
                if u.path == "/":
                    self._send(200, ui_file.read_bytes(), "text/html; charset=utf-8")
                elif u.path == "/api/pages":
                    self._json(app.pages())
                elif u.path == "/api/page":
                    self._json(app.page(q["doc"], int(q["page"])))
                elif u.path.startswith("/img/"):
                    f = IMG_DIR / Path(u.path).name
                    self._send(200, f.read_bytes(), "image/png") if f.exists() else self._send(404, b"", "text/plain")
                else:
                    self._send(404, b"not found", "text/plain")
            except Exception as e:  # 画面に原因を出す
                self._send(500, f"{type(e).__name__}: {e}".encode("utf-8"), "text/plain; charset=utf-8")

        def do_POST(self):
            n = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(n) or b"{}")
            if urlparse(self.path).path == "/api/decide":
                self._json(app.decide(body))
            else:
                self._send(404, b"", "text/plain")

    return H


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="prod1-png-post")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()
    app = App(args.run)
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(app))
    url = f"http://127.0.0.1:{args.port}/"
    print(f"確認画面: {url}  （{len(app.queue)}件 / {len(app.order)}ページ）  終了は Ctrl+C")
    print(f"判定の保存先: reports/review_decisions.{args.run}.json")
    if not args.no_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
