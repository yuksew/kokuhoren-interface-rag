"""Batch API で多数ページを書き起こす（料金 50%、非同期）。

usage:
  uv run python src/batch.py plan    [--config config/pilot.yaml]   # 対象ページ数と費用見積もり（API を呼ばない）
  uv run python src/batch.py submit  [--config ...]                 # 未処理ページを投入（済みのページ・投入中のものは除外）
  uv run python src/batch.py status  [--config ...]
  uv run python src/batch.py collect [--config ...]                 # 終わったバッチの結果を out/{run}/ に保存

状態は out/{run}/batches.json に記録する。出力形式は transcribe.py と同じなので、
postprocess.py / validate.py / report.py がそのまま使える。
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from statistics import mean

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from llm import get_client  # noqa: E402
from pagemeta import doc_profile  # noqa: E402
from pricing import cost_usd  # noqa: E402
from transcribe import build_inputs, load_dotenv, load_manifest, load_prompts, pdf_path, save_result  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MAX_BATCH_BYTES = 150 * 1024 * 1024  # 上限 256MB に対して余裕を持たせる
MAX_BATCH_REQUESTS = 2000


def short(model: str) -> str:
    return model.replace("claude-", "").replace("-", "")


def custom_id(model: str, doc: str, page: int) -> str:
    return f"{short(model)}__{doc}__p{page}"  # ^[a-zA-Z0-9_-]{1,64}$


def parse_custom_id(cid: str, models: list[str]) -> tuple[str, str, int]:
    m, doc, p = cid.split("__")
    model = next(x for x in models if short(x) == m)
    return model, doc, int(p[1:])


def target_pages(cfg: dict, manifest: dict) -> list[tuple[str, int]]:
    out = []
    for doc in cfg["docs"]:
        for p in doc_profile(pdf_path(manifest[doc])):
            if p["has_table"]:
                out.append((doc, p["page"]))
    return out


def load_state(run_dir: Path) -> list[dict]:
    f = run_dir / "batches.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else []


def save_state(run_dir: Path, state: list[dict]) -> None:
    (run_dir / "batches.json").write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")


def pending(cfg: dict, run_dir: Path, pages: list[tuple[str, int]], state: list[dict]) -> list[tuple[str, str, int]]:
    in_flight = {cid for b in state if not b.get("collected") for cid in b["custom_ids"]}
    todo = []
    for model in cfg["models"]:
        for doc, page in pages:
            if (run_dir / model / f"{doc}_p{page}.json").exists():
                continue
            if custom_id(model, doc, page) in in_flight:
                continue
            todo.append((model, doc, page))
    return todo


def cmd_plan(cfg, run_dir, manifest) -> int:
    pages = target_pages(cfg, manifest)
    by_doc = {}
    for d, _ in pages:
        by_doc[d] = by_doc.get(d, 0) + 1
    print("対象（表のあるページ）:", by_doc, "合計", len(pages))
    # 検証（out/anthropic-png）の実測平均で見積もる
    calls = [json.loads(x) for x in (ROOT / "out" / "anthropic-png" / "calls.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    total = 0.0
    for m in cfg["models"]:
        cs = [c for c in calls if c["requested_model"] == m]
        ai, ao = mean(c["usage"]["input_tokens"] for c in cs), mean(c["usage"]["output_tokens"] for c in cs)
        c = cost_usd(m, int(ai), int(ao), batch=True) * len(pages)
        total += c
        print(f"  {m}: 平均 in={ai:,.0f} out={ao:,.0f} tok/頁 → Batch 見積もり ${c:,.2f}")
    print(f"  合計見積もり（Batch）: ${total:,.2f}")
    todo = pending(cfg, run_dir, pages, load_state(run_dir))
    print(f"未処理リクエスト: {len(todo)}")
    return 0


def cmd_submit(cfg, run_dir, manifest) -> int:
    client = get_client("anthropic")
    system, user_tmpl, schema = load_prompts()
    pages = target_pages(cfg, manifest)
    state = load_state(run_dir)
    todo = pending(cfg, run_dir, pages, state)
    if not todo:
        print("投入するものはありません")
        return 0
    chunk, size = [], 0

    def flush():
        nonlocal chunk, size
        if not chunk:
            return
        bid = client.submit_batch(chunk)
        state.append({"id": bid, "custom_ids": [c for c, _ in chunk], "created_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                      "collected": False})
        save_state(run_dir, state)
        print(f"submitted {bid}: {len(chunk)} requests, {size / 1e6:.0f}MB")
        chunk, size = [], 0

    for model, doc, page in todo:
        atts, user_text = build_inputs(manifest[doc], page, cfg["input"], cfg["dpi"], user_tmpl)
        req_size = sum(len(a.data) for a in atts) * 4 // 3 + 40_000
        if chunk and (size + req_size > MAX_BATCH_BYTES or len(chunk) >= MAX_BATCH_REQUESTS):
            flush()
        chunk.append((custom_id(model, doc, page), dict(
            model=model, system=system, user_text=user_text, attachments=atts, schema=schema,
            max_tokens=cfg["max_tokens"], effort=cfg["effort"])))
        size += req_size
    flush()
    return 0


def cmd_status(cfg, run_dir, manifest) -> int:
    client = get_client("anthropic")
    for b in load_state(run_dir):
        st = client.batch_status(b["id"])
        print(b["id"], len(b["custom_ids"]), st["status"], st["counts"], "collected" if b.get("collected") else "")
    return 0


def cmd_collect(cfg, run_dir, manifest) -> int:
    client = get_client("anthropic")
    state = load_state(run_dir)
    errors = 0
    for b in state:
        if b.get("collected"):
            continue
        st = client.batch_status(b["id"])
        if st["status"] != "ended":
            print(f"{b['id']}: まだ処理中 {st['counts']}")
            continue
        n = 0
        for item in client.batch_results(b["id"]):
            model, doc, page = parse_custom_id(item.custom_id, cfg["models"])
            if item.result is None:
                errors += 1
                print(f"  ERROR {item.custom_id}: {item.error}", file=sys.stderr)
                continue
            save_result(run_dir, manifest[doc], {"doc_id": doc, "page": page, "category": []}, model, item.result,
                        provider="anthropic", input_kind=cfg["input"], effort=cfg["effort"], batch=True, batch_id=b["id"])
            n += 1
        b["collected"] = True
        b["collected_at"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        save_state(run_dir, state)
        print(f"{b['id']}: {n} 件保存")
    if errors:
        print(f"{errors} 件のエラー。もう一度 submit すると未処理分だけ再投入する", file=sys.stderr)
    return 1 if errors else 0


def main() -> int:
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["plan", "submit", "status", "collect"])
    ap.add_argument("--config", default="config/pilot.yaml")
    args = ap.parse_args()
    cfg = yaml.safe_load((ROOT / args.config).read_text(encoding="utf-8"))
    run_dir = ROOT / "out" / cfg["run"]
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    return {"plan": cmd_plan, "submit": cmd_submit, "status": cmd_status, "collect": cmd_collect}[args.command](cfg, run_dir, manifest)


if __name__ == "__main__":
    sys.exit(main())
