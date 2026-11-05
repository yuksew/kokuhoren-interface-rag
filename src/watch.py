"""新着の確認: sources/watch.yaml の掲載ページを見て、前回から増えたリンク（資料・ページ）を一覧にする。API は使わない。

usage: uv run python src/watch.py [--only kaigo_if shogai_if] [--dry-run]
  sources/watch_state.json に、ページごとに見たリンク（URL と文字）を残す。初めて見るページは記録だけして、新着としては出さない。
  新着があれば reports/watch/{日付}.md に書き、終了コード 10 で終わる（定期実行や CI で気づけるように）。
  --dry-run: 状態を書き換えない（確認だけ）
見つけたら何をするかは docs/revision_runbook.md。
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
import time
import unicodedata
from pathlib import Path
from urllib.parse import urljoin

import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "sources" / "watch.yaml"
STATE = ROOT / "sources" / "watch_state.json"
OUT = ROOT / "reports" / "watch"
UA = "kokuhoren-interface-rag watch (public document monitor)"


def decode(resp: requests.Response) -> str:
    """WAM NET は Shift_JIS、厚労省・こども家庭庁は UTF-8。ヘッダー・meta の charset を見て、バイト列から自分で直す
    （requests の推測に任せると、文字化けした題名が状態に残り、直したときにすべて「新着」に見える）"""
    raw = resp.content
    meta = re.search(rb"charset=[\"']?([A-Za-z0-9_-]+)", raw[:4000])
    head = re.search(r"charset=([A-Za-z0-9_-]+)", resp.headers.get("content-type", ""))
    enc = (meta.group(1).decode() if meta else head.group(1) if head else "utf-8").lower()
    if enc in ("shift_jis", "shift-jis", "sjis", "x-sjis", "windows-31j"):
        enc = "cp932"
    return raw.decode(enc, errors="replace")


# どのページにもあるサイトの案内のリンク（新着ではない）
SITE_NAV = r"^(診療報酬改定|消費税と診療報酬について|所管の法令、告示・通達等|審議会・研究会等|覚書等)$"


def plain(s: str) -> str:
    return unicodedata.normalize("NFKC", re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip())


def links(page_url: str, text: str, include: str | None, exclude: str | None) -> list[dict]:
    """ページのリンク（絶対 URL・文字）。同じ URL は最初の文字だけ。
    「資料」「[PDF][89KB]」のような短い文字のリンクは、直前の文字（会議名・資料名）を前に付ける"""
    out, seen = [], set()
    for m in re.finditer(r"<a\s[^>]*href=\"([^\"#][^\"]*)\"[^>]*>(.*?)</a>", text, re.S | re.I):
        url = urljoin(page_url, html.unescape(m.group(1)).strip())
        title = plain(m.group(2))
        if not title or url in seen or url.startswith(("javascript:", "mailto:")) or re.search(SITE_NAV, title):
            continue
        short = len(re.sub(r"\[[^\]]*\]", "", title)) <= 6
        # include・exclude は、リンクの文字か URL のどちらかに当てる（「資料$」のように文字の終わりで見たいとき用）
        if include and not (re.search(include, title) or re.search(include, url)):
            continue
        if exclude and (re.search(exclude, title) or re.search(exclude, url)):
            continue
        if short:
            ctx = text[max(0, m.start() - 600):m.start()]
            ctx = re.sub(r"^[^<]*?>", "", ctx)   # 途中で切れたタグの残り
            before = plain(re.sub(r"<a\s.*?</a>", " ", ctx, flags=re.S | re.I))
            title = f"{before[-60:]} {title}".strip()
        seen.add(url)
        out.append({"url": url, "title": title[:200]})
    return out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    pages = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    today = dt.date.today().isoformat()
    new_items, errors, seeded = [], [], []
    for p in pages:
        if args.only and p["id"] not in args.only:
            continue
        try:
            resp = requests.get(p["url"], headers={"User-Agent": UA}, timeout=60)
            resp.raise_for_status()
        except Exception as ex:  # noqa: BLE001
            errors.append(f"{p['id']}: 取得できない（{ex}）")
            continue
        found = links(p["url"], decode(resp), p.get("include"), p.get("exclude"))
        if not found:
            errors.append(f"{p['id']}: リンクが 1 つも無い（ページの作りが変わった？ include を見直す）")
        old = state.get(p["id"])
        known = {x["url"] for x in (old or {}).get("links", [])}
        added = [x for x in found if x["url"] not in known]
        if old is None:
            seeded.append(f"{p['id']}: {len(found)} 件を記録（初回）")
        else:
            new_items += [{**x, "page": p["id"], "label": p["label"]} for x in added]
        prev = {x["url"]: x for x in (old or {}).get("links", [])}
        state[p["id"]] = {"url": p["url"], "checked_at": today,
                          "links": [{**x, "first_seen": prev.get(x["url"], {}).get("first_seen", today)} for x in found]
                                   + [x for u, x in prev.items() if u not in {y["url"] for y in found}]}
        print(f"{p['id']}: {len(found)} 件" + (f"、新着 {len(added)} 件" if old is not None and added else ""))
        time.sleep(1)
    for s in seeded:
        print("  " + s)
    for e in errors:
        print("  ! " + e, file=sys.stderr)
    if not args.dry_run:
        STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    if not new_items:
        print("新着なし")
        return 1 if errors else 0
    lines = [f"# 新着（{today}）", "", "取り込むかどうかは docs/revision_runbook.md の「1. 判定」を見る。", ""]
    for pid in dict.fromkeys(x["page"] for x in new_items):
        xs = [x for x in new_items if x["page"] == pid]
        lines += [f"## {xs[0]['label']}", ""] + [f"- [{x['title']}]({x['url']})" for x in xs] + [""]
    print("\n".join(lines))
    if not args.dry_run:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / f"{today}.md").write_text("\n".join(lines), encoding="utf-8")
        print(f"→ {(OUT / f'{today}.md').relative_to(ROOT)}")
    return 10


if __name__ == "__main__":
    sys.exit(main())
