"""算定ルール資料の PDF のうち、文字の無い（画像だけの）ページを Claude で書き起こす（API を使う）。

usage: uv run python src/ocr_rules.py [--model claude-sonnet-5-5] [--only kaigo_qa_r6_v11] [--dry-run]
- 対象: sources/rules_manifest.yaml の ingest: prose の PDF で、テキストレイヤの文字が無いページ。
- 結果: out/ocr_rules/{doc_id}_p{page}.json（本文・モデル・原本の sha256・費用）。build_rules.py が、
  文字の無いページの代わりにこれを読む。すでにあるページは呼ばない（--force でやり直す）。
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

import pymupdf
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from llm import get_client  # noqa: E402
from llm.base import Attachment  # noqa: E402
from pricing import cost_usd  # noqa: E402
from transcribe import load_dotenv  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out" / "ocr_rules"
SYSTEM = """あなたは、厚生労働省などが出した行政文書のページ画像を、そのままテキストに書き起こす係です。
- 画像にある文字を、上から順に、書かれているとおりに書き起こす。要約・言い換え・補足をしない。
- 見出し・「問N」「（答）」・番号付きの項目は、それぞれ行を分ける。段落の中の改行はつなげてよい。
- 表は、1行を1行にして、セルを「 | 」で区切る。
- ページ番号・ページの端の飾りは書かない。
- 読めない文字は〓にする。推測で補わない。"""
SCHEMA = {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"], "additionalProperties": False}


def blank_pages(path: Path) -> list[int]:
    with pymupdf.open(path) as d:
        return [i + 1 for i, pg in enumerate(d) if not pg.get_text().strip()]


def ocr_path(doc_id: str, page: int) -> Path:
    return OUT / f"{doc_id}_p{page}.json"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="claude-sonnet-5-5")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    entries = yaml.safe_load((ROOT / "sources" / "rules_manifest.yaml").read_text(encoding="utf-8"))
    entries = entries.get("entries", entries) if isinstance(entries, dict) else entries
    todo = []
    for e in entries:
        if e.get("format") != "pdf" or e.get("ingest") != "prose" or (args.only and e["id"] not in args.only):
            continue
        f = ROOT / "sources" / "raw" / "rules" / e["domain"] / f"{e['id']}.pdf"
        if not f.exists():
            continue
        todo += [(e, f, p) for p in blank_pages(f) if args.force or not ocr_path(e["id"], p).exists()]
    print(f"文字の無いページ（未処理）: {len(todo)}")
    for e, f, p in todo:
        print(f"  {e['id']} p{p}")
    if args.dry_run or not todo:
        return 0
    load_dotenv()
    client = get_client("anthropic")
    OUT.mkdir(parents=True, exist_ok=True)
    total = 0.0
    for e, f, p in todo:
        with pymupdf.open(f) as d:
            png = d[p - 1].get_pixmap(dpi=args.dpi).tobytes("png")
        res = client.generate_json(model=args.model, system=SYSTEM, user_text="このページを書き起こしてください。",
                                   attachments=[Attachment("png", png)], schema=SCHEMA, max_tokens=8000)
        u = res.usage
        cost = cost_usd(args.model, u.input_tokens, u.output_tokens, u.cache_creation_input_tokens, u.cache_read_input_tokens)
        total += cost
        text = (res.parsed or {}).get("text") or ""
        ocr_path(e["id"], p).write_text(json.dumps({
            "doc_id": e["id"], "page": p, "text": text, "model": res.model, "dpi": args.dpi,
            "source_sha256": hashlib.sha256(f.read_bytes()).hexdigest(), "stop_reason": res.stop_reason,
            "usage": u.__dict__, "cost_usd": round(cost, 6), "request_id": res.request_id,
            "created_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  {e['id']} p{p}: {len(text)} 字 / {res.stop_reason} / ${cost:.4f}")
    print(f"費用 ${total:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
