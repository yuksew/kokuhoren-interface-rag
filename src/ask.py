"""質問に、検索した仕様書・算定ルール資料の抜粋だけを根拠にして答える（Claude API）。

usage: uv run --group rag python src/ask.py "受給者証番号の桁数は？" [--domain shogai] [--exchange J611] [--model claude-sonnet-5-5] [-k 12]
  前提: build_db.py → build_index.py、.env に ANTHROPIC_API_KEY
- 抜粋に番号を振って渡し、モデルには番号で引用させる。出典（文書・版・ページ）は DB から表示するので、
  モデルがページ番号を作ることはない。
- 1回ごとのトークンと費用を out/answers/calls.jsonl に記録する。
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from collections import Counter
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from llm import get_client  # noqa: E402
from pricing import cost_usd  # noqa: E402
from retrieve import Retriever  # noqa: E402
from transcribe import load_dotenv  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DOMAIN = {"kaigo": "介護", "shogai": "障害"}
LOG = ROOT / "out" / "answers" / "calls.jsonl"


def load_prompts() -> tuple[str, dict]:
    return ((ROOT / "prompts" / "answer_system.md").read_text(encoding="utf-8"),
            json.loads((ROOT / "prompts" / "answer.schema.json").read_text(encoding="utf-8")))


def source_label(r: Retriever, hit: dict) -> str:
    """抜粋の出典（DB から作る）。"""
    if hit["kind"] == "overview":
        return "インタフェース一覧とレコード表の表題から作成した、交換情報ごとのレコード構成"
    if hit["kind"] in ("rule", "svc"):
        x = r.con.execute("SELECT c.page, c.sc_from, c.sc_to, d.title, d.edition FROM chunks c JOIN rule_docs d USING (doc_id) "
                          "WHERE chunk_id = ?", (hit["chunk_id"],)).fetchone()
        dom = DOMAIN.get(hit["domain"], "")
        if hit["kind"] == "rule":
            return f"{dom} {x['title']}（{x['edition']}） p{x['page']}"
        s = r.con.execute("SELECT sheet, min(row) a, max(row) b FROM service_codes WHERE sc_id BETWEEN ? AND ?",
                          (x["sc_from"], x["sc_to"])).fetchone()
        return f"{dom} {x['title']}（{x['edition']}） シート「{s['sheet']}」 {s['a']}〜{s['b']}行"
    if hit["kind"] == "prose":
        x = r.con.execute("SELECT c.page, c.printed_page, d.domain, d.volume, d.edition FROM chunks c JOIN documents d USING (doc_id) "
                          "WHERE chunk_id = ?", (hit["chunk_id"],)).fetchone()
        pp = f"（印刷 {x['printed_page']}）" if x["printed_page"] else ""
        return f"{DOMAIN[x['domain']]} {x['volume']} {x['edition']} PDF p{x['page']}{pp}（本文）"
    if hit["item_id"] is not None:
        x = r.con.execute("SELECT * FROM v_items WHERE item_id = ?", (hit["item_id"],)).fetchone()
        pp = f"（印刷 {x['printed_page']}）" if x["printed_page"] else ""
        return (f"{DOMAIN[x['domain']]} {x['volume']} {x['edition']} PDF p{x['page']}{pp}"
                f" 「{x['table_title'] or '表題なし'}」 項番 {x['no_raw'] or x['no'] or '-'} {x['name_full'] or ''}")
    t = r.con.execute("SELECT t.*, d.domain, d.volume, d.edition FROM spec_tables t JOIN documents d USING (doc_id) "
                      "WHERE table_id = ?", (hit["table_id"],)).fetchone()
    return f"{DOMAIN[t['domain']]} {t['volume']} {t['edition']} PDF p{t['page_from']}〜{t['page_to']} 「{t['title'] or '表題なし'}」（表全体）"


LIST_Q = re.compile(r"項目|構成|一覧|レイアウト|どんな|並び|全部")
# 交換情報・レコードの全体像を聞く質問（「請求の CSV の構造」「どの CSV に何を設定」）
STRUCT_Q = re.compile(r"構造|どのCSV|どの CSV|どのレコード|何を送る|どんなファイル|どのような CSV|どのようなCSV")
REWRITE_MODEL = "claude-haiku-5-5"


def rewrite(question: str, client, domain: str | None = None, model: str = REWRITE_MODEL) -> tuple[list[str], float, dict]:
    """検索の前に、質問を資料の言葉づかいの検索文（最大3つ）に言い換える。(検索文, 費用, usage)"""
    system = (ROOT / "prompts" / "rewrite_system.md").read_text(encoding="utf-8")
    schema = json.loads((ROOT / "prompts" / "rewrite.schema.json").read_text(encoding="utf-8"))
    res = client.generate_json(model=model, system=system, user_text=f"# 質問\n{question}" + (f"\n（対象: {DOMAIN[domain]}）" if domain else ""), attachments=[], schema=schema,
                               max_tokens=400)
    qs = [q.strip() for q in ((res.parsed or {}).get("queries") or []) if isinstance(q, str) and q.strip()][:3]
    u = res.usage
    return qs, cost_usd(model, u.input_tokens, u.output_tokens, u.cache_creation_input_tokens, u.cache_read_input_tokens), u.__dict__


def table_listing(r: Retriever, table_id: int, max_rows: int = 200) -> str:
    """表全体の行一覧（表単位の質問用）。表のチャンクの見出しに、行を1行ずつ並べる。"""
    head = [ln for ln in r.describe_table(table_id).splitlines() if not ln.startswith("項目: ")]
    rows = r.con.execute("SELECT no_raw, no, name_full, type, length_raw, length, required, content FROM items "
                         "WHERE table_id = ? ORDER BY seq LIMIT ?", (table_id, max_rows)).fetchall()
    lines = []
    for x in rows:
        spec = "".join(f" / {lab} {v}" for lab, v in (("属性", x["type"]), ("桁数", x["length_raw"] or x["length"]),
                                                       ("必須", x["required"])) if v)
        first = (x["content"] or "").splitlines()[0][:60] if x["content"] else ""
        lines.append(f"項番 {x['no_raw'] or x['no'] or '-'} {x['name_full'] or '（項目名なし）'}{spec}" + (f" / 内容 {first}" if first else ""))
    return "\n".join(head + ["行一覧:"] + lines)


def answer(question: str, *, r: Retriever, client, model: str, domain: str | None = None, exchange: str | None = None,
           k: int = 12, max_tokens: int = 2000, log_extra: dict | None = None, use_rewrite: bool = True) -> dict:
    system, schema = load_prompts()
    queries, rw_cost, rw_usage = (rewrite(question, client, domain) if use_rewrite else ([], 0.0, None))
    hits = r.search_multi([question] + queries, k=k, domain=domain, exchange=exchange)
    # 全体像の質問には、交換情報ごとのレコード構成の一覧を先頭に入れる
    overview = None
    if STRUCT_Q.search(question):
        overview = r.exchange_overview([question] + queries, hits, domain)
    if overview:
        hits = [{"kind": "overview", "chunk_id": None, "item_id": None, "table_id": None, "domain": domain,
                 "via": ["overview"], "text": overview}] + hits[: k - 1]
    # 「〇〇レコードの項目は？」「構成は？」のような質問では、行の抜粋だけでは全体が分からないので、
    # 上位5件にある表（無ければ上位で最も多く出てくる表）を、行一覧ごと先頭に入れる
    if LIST_Q.search(question) and hits:
        tid = next((h["table_id"] for h in hits[:5] if h["kind"] == "table"), None)
        if tid is None:
            tid = next(iter(Counter(h["table_id"] for h in hits if h["table_id"] is not None).most_common(1)), (None,))[0]
        tchunk = next((m for m in r.meta if m["kind"] == "table" and m["table_id"] == tid), None)
        if tchunk:
            hits = [{**tchunk, "score": 0.0, "via": ["table-expand"], "expand": True}] + \
                   [h for h in hits if h["chunk_id"] != tchunk["chunk_id"]][: k - 1]

    def text(i, h):
        if h.get("expand"):
            return f"[{i}] (表全体)\n{table_listing(r, h['table_id'])}"
        if h["kind"] == "overview":
            return f"[{i}] (交換情報の構成)\n{h['text']}"
        label = {"table": "表", "item": "行", "prose": "本文", "rule": "算定ルール", "svc": "サービスコード表"}[h["kind"]]
        return f"[{i}] ({label})\n{r.describe(h['chunk_id'])}"
    ctx = "\n\n".join(text(i, h) for i, h in enumerate(hits, 1))
    cond = "、".join(x for x in [f"対象: {DOMAIN[domain]}" if domain else "", f"交換情報識別番号: {exchange}" if exchange else ""] if x)
    user = f"# 抜粋\n{ctx}\n\n# 質問\n{question}" + (f"\n（{cond}）" if cond else "")
    res = client.generate_json(model=model, system=system, user_text=user, attachments=[], schema=schema,
                               max_tokens=max_tokens, effort="low")
    p = res.parsed or {"answer": res.text, "used": [], "insufficient": True}
    cited = sorted({int(n) for n in re.findall(r"\[(\d+)\]", p.get("answer") or "")} | set(p.get("used") or []))
    bad = [n for n in cited if not 1 <= n <= len(hits)]
    u = res.usage
    cost = cost_usd(model, u.input_tokens, u.output_tokens, u.cache_creation_input_tokens, u.cache_read_input_tokens) + rw_cost
    out = {
        "question": question, "domain": domain, "exchange": exchange, "model": model,
        "answer": p.get("answer"), "insufficient": p.get("insufficient"), "cited": [n for n in cited if n not in bad],
        "invalid_citations": bad,
        "sources": {n: {"label": source_label(r, hits[n - 1]), "item_id": hits[n - 1]["item_id"], "table_id": hits[n - 1]["table_id"]}
                    for n in cited if n not in bad},
        "retrieved": [{"item_id": h["item_id"], "table_id": h["table_id"], "via": h["via"]} for h in hits],
        "queries": queries, "rewrite_usage": rw_usage,
        "usage": u.__dict__, "cost_usd": round(cost, 6), "latency_s": round(res.latency_s, 2),
        "stop_reason": res.stop_reason, "request_id": res.request_id,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        **(log_extra or {}),
    }
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps({k_: v for k_, v in out.items() if k_ != "retrieved"}, ensure_ascii=False) + "\n")
    return out


def render(a: dict) -> str:
    lines = [a["answer"] or "", ""]
    if a["insufficient"]:
        lines.append("（※ 抜粋だけでは十分に答えられない、とモデルが判断しました）")
    if a["sources"]:
        lines.append("出典:")
        lines += [f"  [{n}] {s['label']}" for n, s in sorted(a["sources"].items())]
    if a["invalid_citations"]:
        lines.append(f"（存在しない抜粋番号の引用: {a['invalid_citations']}）")
    u = a["usage"]
    lines.append(f"\n{a['model']} / 入力 {u['input_tokens']:,} 出力 {u['output_tokens']:,} トークン / ${a['cost_usd']:.4f} / {a['latency_s']} 秒")
    return "\n".join(lines)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    ap.add_argument("--domain", choices=["kaigo", "shogai"])
    ap.add_argument("--exchange")
    ap.add_argument("--model", default="claude-sonnet-5-5", help="既定は Sonnet（Haiku は1/20の費用だが、属性や項目の取り違えがある。reports/phase2_report.md）")
    ap.add_argument("-k", type=int, default=12)
    args = ap.parse_args()
    a = answer(args.question, r=Retriever(), client=get_client("anthropic"), model=args.model,
               domain=args.domain, exchange=args.exchange, k=args.k)
    print(render(a))
    return 0


if __name__ == "__main__":
    sys.exit(main())
