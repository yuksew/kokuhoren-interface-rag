"""仕様書の「設定例」（実際の提供の図 → インタフェース設定の表 → 説明）を、事例ごとに構造化して書き起こす。

usage: uv run python src/transcribe_examples.py --doc shogai_jigyosho_r0710 --pages 161,176,197 [--models haiku,sonnet]
  - ページ画像（PNG）を Haiku と Sonnet の両方に渡し、out/examples/{doc}/{model}/p{page}.json に書く（API を使う）。
  - 既にあるページは飛ばす（--force で書き直す）。
  - スキーマと指示は prompts/{kind}.schema.json・prompts/{kind}_system.md。
  - --kind daysettings: 「日数情報レコードの設定方法」のような、サービス種類｜事務処理要領｜データ設定例 の表
    （out/daysettings/{doc}/{model}/p{page}.json。build_daysettings.py が読む）
"""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from llm import get_client  # noqa: E402
from llm.base import Attachment  # noqa: E402
from pricing import cost_usd  # noqa: E402
from transcribe import load_dotenv, load_manifest, pdf_path, render_png  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MODELS = {"haiku": "claude-haiku-5-5", "sonnet": "claude-sonnet-5-5"}


def parse_pages(s: str) -> list[int]:
    out: list[int] = []
    for part in s.split(","):
        a, _, b = part.partition("-")
        out += list(range(int(a), int(b or a) + 1))
    return out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", required=True)
    ap.add_argument("--pages", required=True, help="例: 161,176 / 161-210")
    ap.add_argument("--models", default="haiku,sonnet")
    ap.add_argument("--dpi", type=int, default=150)
    ap.add_argument("--effort", default="medium")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--kind", default="examples", choices=["examples", "daysettings"])
    args = ap.parse_args()
    entry = load_manifest()[args.doc]
    system = (ROOT / "prompts" / f"{args.kind}_system.md").read_text(encoding="utf-8")
    schema = json.loads((ROOT / "prompts" / f"{args.kind}.schema.json").read_text(encoding="utf-8"))
    client = get_client("anthropic")
    jobs = [(m, p) for m in args.models.split(",") for p in parse_pages(args.pages)
            if args.force or not (ROOT / "out" / args.kind / args.doc / m / f"p{p}.json").exists()]

    def run(job):
        m, p = job
        res = client.generate_json(model=MODELS[m], system=system, user_text=f"{entry['title']} の PDF {p} ページです。",
                                   attachments=[Attachment("png", render_png(pdf_path(entry), p, args.dpi))],
                                   schema=schema, max_tokens=16000, effort=args.effort)
        u = res.usage
        cost = cost_usd(MODELS[m], u.input_tokens, u.output_tokens)
        out = ROOT / "out" / args.kind / args.doc / m / f"p{p}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"doc_id": args.doc, "page": p, "model": res.model, "stop_reason": res.stop_reason,
                                   "cost_usd": round(cost, 6), "request_id": res.request_id, "result": res.parsed},
                                  ensure_ascii=False, indent=1), encoding="utf-8")
        r = res.parsed or {}
        n = (f"事例 {len(r.get('examples') or [])} 件" if args.kind == "examples"
             else f"まとまり {sum(len(x['groups']) for x in r.get('sections') or [])} 件")
        print(f"{m:6s} p{p}: {n}, ${cost:.4f}, {res.stop_reason}", flush=True)
        return cost

    with ThreadPoolExecutor(4) as ex:
        total = sum(ex.map(run, jobs))
    print(f"計 {len(jobs)} 件, ${total:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
