"""対象ページを LLM で構造化 JSON に書き起こす（フェーズ1）。

usage:
  uv run python src/transcribe.py                       # 両モデル × config/pages.yaml の全ページ
  uv run python src/transcribe.py --models claude-haiku-5-5 --only kaigo_jigyosho_r0604:80
  uv run python src/transcribe.py --provider mock       # API を呼ばずにパイプラインだけ確認
  uv run python src/transcribe.py --input pdf           # 画像ではなく1ページ切り出しPDFで渡す（比較用）

出力:
  out/{run}/{model}/{doc_id}_p{page}.json   書き起こし結果＋メタ情報
  out/{run}/calls.jsonl                     呼び出しごとのトークン数・概算コスト
  reports/img/{doc_id}_p{page}.png          比較用のページ画像
既存の出力があるページはスキップする（--force で再実行）。
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import sys
from pathlib import Path

import pymupdf
import yaml
from pypdf import PdfReader, PdfWriter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from llm import Attachment, get_client  # noqa: E402
from pricing import cost_usd  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODELS = ["claude-haiku-5-5", "claude-sonnet-5-5"]
DOMAIN_LABEL = {"kaigo": "介護保険", "shogai": "障害福祉（障害者総合支援法・児童福祉法）"}


def load_manifest() -> dict[str, dict]:
    entries = yaml.safe_load((ROOT / "sources" / "manifest.yaml").read_text(encoding="utf-8"))
    return {e["id"]: e for e in entries}


def pdf_path(entry: dict) -> Path:
    return ROOT / "sources" / "raw" / entry["domain"] / f"{entry['id']}.pdf"


def extract_page_pdf(src: Path, page: int) -> bytes:
    """元 PDF から1ページだけを切り出した PDF（元ファイルは変更しない）。"""
    reader = PdfReader(str(src))
    w = PdfWriter()
    w.add_page(reader.pages[page - 1])
    buf = io.BytesIO()
    w.write(buf)
    return buf.getvalue()


def render_png(src: Path, page: int, dpi: int) -> bytes:
    with pymupdf.open(src) as d:
        return d[page - 1].get_pixmap(dpi=dpi).tobytes("png")


def load_dotenv() -> None:
    """プロジェクト直下の .env（KEY=VALUE）を、未設定の環境変数にだけ読み込む。"""
    import os

    f = ROOT / ".env"
    if not f.exists():
        return
    for line in f.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def load_prompts() -> tuple[str, str, dict]:
    system = (ROOT / "prompts" / "transcribe_system.md").read_text(encoding="utf-8")
    user_tmpl = (ROOT / "prompts" / "transcribe_user.md").read_text(encoding="utf-8")
    schema = json.loads((ROOT / "prompts" / "transcribe.schema.json").read_text(encoding="utf-8"))
    return system, user_tmpl, schema


def build_inputs(entry: dict, page: int, input_kind: str, dpi: int, user_tmpl: str,
                 provider: str = "anthropic") -> tuple[list[Attachment], str]:
    """1ページ分の添付とユーザー文。"""
    src = pdf_path(entry)
    if input_kind == "pdf":
        att = Attachment("pdf", extract_page_pdf(src, page))
    else:
        att = Attachment("png", render_png(src, page, dpi=dpi))
    # モックはテキストレイヤを読むので常に PDF も渡す
    atts = [att] if provider != "mock" or att.kind == "pdf" else [Attachment("pdf", extract_page_pdf(src, page)), att]
    user_text = user_tmpl.format(domain_label=DOMAIN_LABEL[entry["domain"]], title=entry["title"],
                                 edition=entry["edition"], page=page)
    return atts, user_text


def save_result(out_dir: Path, entry: dict, spec: dict, model: str, res, *, provider: str,
                input_kind: str, effort: str, batch: bool = False, batch_id: str | None = None) -> dict:
    """書き起こし結果を out/{run}/{model}/{doc_id}_p{page}.json に保存し、calls.jsonl に追記する。"""
    u = res.usage
    cost = cost_usd(model, u.input_tokens, u.output_tokens, u.cache_creation_input_tokens, u.cache_read_input_tokens)
    cost_batch = cost_usd(model, u.input_tokens, u.output_tokens, u.cache_creation_input_tokens,
                          u.cache_read_input_tokens, batch=True)
    meta = {
        "doc_id": spec["doc_id"], "page": spec["page"], "domain": entry["domain"],
        "volume": entry["volume"], "edition": entry["edition"], "title": entry["title"],
        "category": spec.get("category", []), "requested_model": model, "model": res.model,
        "provider": provider, "input": input_kind, "effort": effort,
        "stop_reason": res.stop_reason, "request_id": res.request_id,
        "latency_s": round(res.latency_s, 2),
        "usage": u.__dict__, "cost_usd": round(cost, 6), "cost_usd_batch": round(cost_batch, 6),
        "billed_as": "batch" if batch else "standard", "batch_id": batch_id,
        "parsed_ok": res.parsed is not None,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "stop_details": res.raw.get("stop_details"),
    }
    dest = out_dir / model / f"{spec['doc_id']}_p{spec['page']}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    # スキーマのたたき台にあった domain / edition / volume / page は呼び出し側で付与する
    body = {"domain": entry["domain"], "edition": entry["edition"], "volume": entry["volume"],
            "page": spec["page"], **(res.parsed or {})}
    dest.write_text(json.dumps({"meta": meta, "result": body if res.parsed is not None else None,
                                "raw_text": None if res.parsed is not None else res.text},
                               ensure_ascii=False, indent=2), encoding="utf-8")
    with (out_dir / "calls.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(meta, ensure_ascii=False) + "\n")
    return meta


def main() -> int:
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    ap.add_argument("--provider", default="anthropic", choices=["anthropic", "mock"])
    ap.add_argument("--input", default="png", choices=["pdf", "png"],
                    help="モデルに渡す形式。PDF入力は介護の全角1桁の桁数を落とすため png を既定にした（reports/phase1_report.md）")
    ap.add_argument("--dpi", type=int, default=150, help="--input png のときの解像度")
    ap.add_argument("--effort", default="medium", help="output_config.effort（両モデル共通）")
    ap.add_argument("--max-tokens", type=int, default=64000)
    ap.add_argument("--only", nargs="*", help="doc_id:page で対象を絞る")
    ap.add_argument("--run", help="出力先 out/{run}（既定: {provider}-{input}）")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    manifest = load_manifest()
    pages = yaml.safe_load((ROOT / "config" / "pages.yaml").read_text(encoding="utf-8"))
    if args.only:
        pages = [p for p in pages if f"{p['doc_id']}:{p['page']}" in set(args.only)]
    system, user_tmpl, schema = load_prompts()

    run = args.run or f"{args.provider}-{args.input}"
    out_dir = ROOT / "out" / run
    out_dir.mkdir(parents=True, exist_ok=True)

    client = get_client(args.provider)
    total = 0.0
    failures = 0
    for p in pages:
        entry = manifest[p["doc_id"]]
        key = f"{p['doc_id']}_p{p['page']}"
        atts, user_text = build_inputs(entry, p["page"], args.input, args.dpi, user_tmpl, args.provider)
        for model in args.models:
            if (out_dir / model / f"{key}.json").exists() and not args.force:
                print(f"skip  {model:20s} {key}")
                continue
            print(f"call  {model:20s} {key} ...", flush=True)
            try:
                res = client.generate_json(
                    model=model, system=system, user_text=user_text, attachments=atts,
                    schema=schema, max_tokens=args.max_tokens, effort=args.effort,
                )
            except Exception as e:  # noqa: BLE001
                failures += 1
                print(f"  ERROR {type(e).__name__}: {e}", file=sys.stderr)
                if type(e).__name__ in {"AuthenticationError", "PermissionDeniedError"}:
                    print("認証エラーのため中断します（ANTHROPIC_API_KEY を確認してください）", file=sys.stderr)
                    return 2
                continue
            meta = save_result(out_dir, entry, p, model, res, provider=args.provider,
                               input_kind=args.input, effort=args.effort)
            total += meta["cost_usd"]
            u = res.usage
            print(f"  in={u.input_tokens} out={u.output_tokens} ${meta['cost_usd']:.4f} "
                  f"stop={res.stop_reason} {res.latency_s:.1f}s parsed={res.parsed is not None}")
            if res.stop_reason == "max_tokens":
                print("  WARNING: max_tokens で打ち切られた", file=sys.stderr)

    print(f"\nこの実行の概算コスト合計: ${total:.4f}（通常 API 料金）")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
