"""回答生成の評価: eval/questions.yaml の質問に両モデルで答えさせ、自動の指標と回答本文をまとめる（API を使う）。

usage: uv run --group rag python src/eval_answers.py [--models claude-haiku-5-5 claude-sonnet-5-5] [--out reports/answer_eval.md]
自動の指標
  facts    expect の語がすべて回答に含まれる
  gold     正解の行（または表）を出典として引用した
  invalid  存在しない抜粋番号を引用した
  insufficient  モデルが「抜粋だけでは答えられない」とした
  honest   範囲外の質問（kind: out_of_scope。資料に無いこと）に「答えられない」とした
gold の無い問（範囲外・算定ルール資料の質問）は、正解の行の引用を数えない
回答本文も載せるので、最終的な良し悪しは人が読んで判断する。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ask import answer  # noqa: E402
from eval_retrieval import gold_hits  # noqa: E402
from llm import get_client  # noqa: E402
from retrieve import Retriever  # noqa: E402
from transcribe import load_dotenv  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
AS_OF = "2026-11-05"   # 評価の基準日の既定（施行日をまたいで比べるときは --as-of で変える）


def norm(s) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", str(s or "")))


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=["claude-haiku-5-5", "claude-sonnet-5-5"])
    ap.add_argument("--as-of", default=AS_OF, help="基準日（どの版を今の版とするか）。評価の結果が日付で変わらないよう固定する")
    ap.add_argument("--out", default="reports/answer_eval.md")
    args = ap.parse_args()
    qs = yaml.safe_load((ROOT / "eval" / "questions.yaml").read_text(encoding="utf-8"))
    r, client = Retriever(as_of=args.as_of), get_client("anthropic")
    results = {m: [] for m in args.models}
    for i, q in enumerate(qs, 1):
        gold = gold_hits(r, q.get("gold") or [])
        for m in args.models:
            a = answer(q["q"], r=r, client=client, model=m, domain=q.get("domain"), log_extra={"eval": True})
            text = norm(a["answer"])
            a["facts_ok"] = all(any(norm(alt) in text for alt in e.split("|")) for e in q.get("expect") or []) if q.get("expect") else None
            has_gold = bool(gold)
            a["gold_cited"] = any(gold.match(s) for s in a["sources"].values()) if has_gold else None
            a["gold_retrieved"] = any(gold.match(h) for h in a["retrieved"]) if has_gold else None
            a["honest"] = bool(a["insufficient"]) if q["kind"] == "out_of_scope" else None
            a["kind"] = q["kind"]
            results[m].append(a)
            print(f"{i:2d} {m:18s} facts={a['facts_ok']} gold={a['gold_cited']} ${a['cost_usd']:.4f}", flush=True)
    (ROOT / "out" / "answers").mkdir(parents=True, exist_ok=True)
    (ROOT / "out" / "answers" / "eval_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")

    L = [f"# 回答生成の評価（{len(qs)} 問、基準日 {args.as_of}）", "",
         "抜粋は検索（ハイブリッド＋番号の直接引き、上位12件）。effort=low。facts は expect の語がすべて回答にあるか（expect のある問だけ数える）。", "",
         "| モデル | facts | 正解の行を引用 | 範囲外に「答えられない」 | 範囲内で「答えられない」 | 存在しない番号の引用 | 入力トークン（平均） | 出力トークン（平均） | 費用（合計） | 1問あたり | 応答秒（平均） |",
         "|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|"]
    for m, rs in results.items():
        n = len(rs)
        fx = [x for x in rs if x["facts_ok"] is not None]
        cost = sum(x["cost_usd"] for x in rs)
        gx = [x for x in rs if x["gold_cited"] is not None]
        hx = [x for x in rs if x["honest"] is not None]
        L.append(f"| {m} | {sum(x['facts_ok'] for x in fx)}/{len(fx)} | {sum(x['gold_cited'] for x in gx)}/{len(gx)} | "
                 f"{sum(x['honest'] for x in hx)}/{len(hx)} | {sum(bool(x['insufficient']) for x in rs if x['honest'] is None)} | "
                 f"{sum(bool(x['invalid_citations']) for x in rs)} | "
                 f"{sum(x['usage']['input_tokens'] for x in rs) / n:,.0f} | {sum(x['usage']['output_tokens'] for x in rs) / n:,.0f} | "
                 f"${cost:.3f} | ${cost / n:.4f} | {sum(x['latency_s'] for x in rs) / n:.1f} |")
    L += ["", "正解の行を引用しなかった問・facts を外した問・範囲外なのに答えた問", ""]
    for m, rs in results.items():
        bad = [f"「{x['question']}」" + ("（facts×）" if x["facts_ok"] is False else "") +
               ("（正解が検索結果にあるのに引用せず）" if x["gold_retrieved"] and not x["gold_cited"] else "") +
               ("（正解が検索結果に無い）" if x["gold_retrieved"] is False else "") +
               ("（範囲外なのに答えた）" if x["honest"] is False else "")
               for x in rs if x["facts_ok"] is False or x["gold_cited"] is False or x["honest"] is False]
        L.append(f"- {m}: " + ("、".join(bad) if bad else "なし"))
    L += ["", "## 回答本文", ""]
    for i, q in enumerate(qs):
        L.append(f"### {i + 1}. {q['q']}（{q.get('domain')}・{q['kind']}）")
        for m in args.models:
            x = results[m][i]
            mk = lambda v: "○" if v else "×" if v is False else "-"
            marks = f"facts={mk(x['facts_ok'])} 引用={mk(x['gold_cited'])}" + (f" 答えられない={mk(x['honest'])}" if x["honest"] is not None else "")
            L.append(f"**{m}**（{marks}）")
            L.append("")
            L.append("> " + (x["answer"] or "").replace("\n", "\n> "))
            if x["sources"]:
                L.append("")
                L += [f"- [{n}] {s['label']}" for n, s in sorted(x["sources"].items(), key=lambda kv: int(kv[0]))][:6]
            L.append("")
    (ROOT / args.out).write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:12]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
