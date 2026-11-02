"""社内で試すための質問画面（ブラウザ）。ask.py の answer() をそのまま使う（API を使う）。

usage: uv run --group rag python src/web_app.py [--port 8080]
  - ローカルでは http://127.0.0.1:8080/ を開く。Cloud Run では環境変数 PORT で待ち受ける（README の「社内で試す」）。
  - 環境変数:
      ANTHROPIC_API_KEY  必須（ローカルでは .env、Cloud Run では Secret Manager から渡す）
      ANSWER_MODEL       回答のモデル（既定 claude-sonnet-5-5）
      MAX_USD_PER_DAY    1日（UTC）の API 費用の上限（既定 5）。超えたらその日は答えない
      LOG_QUESTIONS      1 にすると、質問文もログ（標準出力）に出す。既定は費用・時間・利用者だけ
- ログは標準出力に1行1件の JSON で出す（Cloud Run では Cloud Logging に入る）。
- 利用者は IAP が付けるヘッダ（X-Goog-Authenticated-User-Email）から取る。ローカルでは空。
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ask  # noqa: E402
from llm import get_client  # noqa: E402
from retrieve import Retriever  # noqa: E402
from transcribe import load_dotenv  # noqa: E402

UI = Path(__file__).resolve().parent / "web_ui.html"
ask.LOG = None  # 回答の記録は out/ ではなく標準出力へ（下の log）


class Budget:
    """1日の費用の上限（インスタンスごとの概算。Cloud Run は max-instances 1 で使う前提）。"""

    def __init__(self, limit: float):
        self.limit, self.day, self.spent, self.lock = limit, None, 0.0, threading.Lock()

    def _roll(self):
        today = dt.datetime.now(dt.timezone.utc).date()
        if self.day != today:
            self.day, self.spent = today, 0.0

    def ok(self) -> bool:
        with self.lock:
            self._roll()
            return self.spent < self.limit

    def add(self, usd: float) -> None:
        with self.lock:
            self._roll()
            self.spent += usd


def log(**kw) -> None:
    print(json.dumps({"time": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), **kw}, ensure_ascii=False), flush=True)


def make_handler(r: Retriever, client, model: str, budget: Budget, log_questions: bool):
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

        def _json(self, code: int, obj):
            self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                self._send(200, UI.read_bytes(), "text/html; charset=utf-8")
            elif self.path == "/healthz":
                self._send(200, b"ok", "text/plain")
            else:
                self._send(404, b"not found", "text/plain")

        def do_POST(self):
            if self.path != "/api/ask":
                return self._send(404, b"", "text/plain")
            user = (self.headers.get("X-Goog-Authenticated-User-Email") or "").removeprefix("accounts.google.com:")
            try:
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
            except ValueError:
                return self._json(400, {"error": "リクエストの形が正しくありません"})
            q = (body.get("question") or "").strip()
            domain = body.get("domain") if body.get("domain") in ("kaigo", "shogai") else None
            if not q or len(q) > 1000:
                return self._json(400, {"error": "質問は1〜1000文字で入力してください"})
            if not budget.ok():
                log(event="budget_exceeded", user=user)
                return self._json(429, {"error": "今日の利用額の上限に達しました。明日（日本時間の午前9時以降）にもう一度試してください"})
            try:
                a = ask.answer(q, r=r, client=client, model=model, domain=domain)
            except Exception as e:  # API の失敗などは画面に出し、ログにも残す
                log(event="error", user=user, error=f"{type(e).__name__}: {e}")
                return self._json(500, {"error": "回答の作成に失敗しました。少し待ってからもう一度試してください"})
            budget.add(a["cost_usd"])
            log(event="answer", user=user, domain=domain, cost_usd=a["cost_usd"], latency_s=a["latency_s"],
                insufficient=a["insufficient"], invalid_citations=a["invalid_citations"], request_id=a["request_id"], **({"question": q} if log_questions else {}))
            self._json(200, {"answer": a["answer"], "insufficient": a["insufficient"], "invalid_citations": a["invalid_citations"],
                             "sources": [{"n": n, "label": s["label"], "link": s.get("link")} for n, s in sorted(a["sources"].items())],
                             "cost_usd": a["cost_usd"]})

    return H


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8080")))
    ap.add_argument("--host", default="0.0.0.0" if os.environ.get("K_SERVICE") else "127.0.0.1")
    args = ap.parse_args()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY が設定されていません", file=sys.stderr)
        return 1
    r = Retriever()  # 埋め込みモデルと DB は起動時に1回だけ読む
    client = get_client("anthropic")
    model = os.environ.get("ANSWER_MODEL", "claude-sonnet-5-5")
    budget = Budget(float(os.environ.get("MAX_USD_PER_DAY", "5")))
    srv = ThreadingHTTPServer((args.host, args.port), make_handler(r, client, model, budget, os.environ.get("LOG_QUESTIONS") == "1"))
    log(event="start", host=args.host, port=args.port, model=model, device=getattr(r.emb, "device", None))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
