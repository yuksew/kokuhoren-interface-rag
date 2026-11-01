"""実際の質問での評価: eval/real_questions.txt の質問に答え、人が判定するための CSV を作る（API を使う）。

usage:
  uv run --group rag python src/eval_real.py run       # 回答して reports/real_eval.csv を作る（1問 約 $0.01、Sonnet）
  uv run --group rag python src/eval_real.py summary   # 判定を記入した CSV を集計する
CSV の「判定」列に ○（正しい）・△（一部正しい・不足）・×（誤り）を、「コメント」に気づいたことを書く。
すでに回答済みの質問は run をやり直しても回答し直さない（判定は残る）。--force で全部やり直す。
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent
QFILE = ROOT / "eval" / "real_questions.txt"
OUT = ROOT / "reports" / "real_eval.csv"
COLS = ["質問", "対象", "判定", "コメント", "回答", "出典", "答えられない", "モデル", "費用USD"]
DOMAIN = {"介護": "kaigo", "障害": "shogai"}


def read_questions() -> list[tuple[str, str | None]]:
    out = []
    for ln in QFILE.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        dom = None
        for k, v in DOMAIN.items():
            for sep in (":", "："):
                if ln.startswith(k + sep):
                    dom, ln = v, ln[len(k) + 1:].strip()
        out.append((ln, dom))
    return out


def load_csv() -> list[dict]:
    if not OUT.exists():
        return []
    with OUT.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def cmd_run(model: str, force: bool) -> int:
    from ask import answer
    from llm import get_client
    from retrieve import Retriever
    from transcribe import load_dotenv

    load_dotenv()
    qs = read_questions()
    if not qs:
        print(f"{QFILE.relative_to(ROOT)} に質問がありません")
        return 1
    old = {(r["質問"], r["対象"]): r for r in load_csv()} if not force else {}
    r, client = Retriever(), get_client("anthropic")
    rows, cost = [], 0.0
    for q, dom in qs:
        key = (q, {"kaigo": "介護", "shogai": "障害"}.get(dom, "両方"))
        if key in old:
            rows.append(old[key])
            continue
        a = answer(q, r=r, client=client, model=model, domain=dom, log_extra={"eval_real": True})
        cost += a["cost_usd"]
        rows.append({"質問": q, "対象": key[1], "判定": "", "コメント": "", "回答": a["answer"],
                     "出典": "\n".join(f"[{n}] {s['label']}" for n, s in sorted(a["sources"].items())),
                     "答えられない": "はい" if a["insufficient"] else "", "モデル": model, "費用USD": f"{a['cost_usd']:.4f}"})
        print(f"・{q[:40]}  ${a['cost_usd']:.4f}", flush=True)
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} 問（新たに回答 ${cost:.3f}）→ {OUT.relative_to(ROOT)}  判定列に ○ △ × を記入してください")
    return 0


def cmd_summary() -> int:
    rows = load_csv()
    c = Counter((r["判定"] or "未記入").strip() for r in rows)
    print(f"{len(rows)} 問: " + "、".join(f"{k} {v}" for k, v in c.most_common()))
    for r in rows:
        if (r["判定"] or "").strip() in ("×", "△"):
            print(f"  [{r['判定']}] {r['質問']}  — {r['コメント']}")
    return 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["run", "summary"])
    ap.add_argument("--model", default="claude-sonnet-5-5")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    return cmd_run(args.model, args.force) if args.command == "run" else cmd_summary()


if __name__ == "__main__":
    sys.exit(main())
