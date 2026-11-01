"""モデル別単価（USD / 100万トークン）。

出典: Anthropic 公式の料金表（claude-api スキル同梱のモデル表, 2026-10-06 時点のキャッシュ）。
- claude-haiku-5-5 : 入力 $0.10 / 出力 $0.50（プロンプト 100K トークン以下。超えると $0.50 / $2.50）
- claude-sonnet-5-5: 入力 $2.00 / 出力 $10.00
- Batch API は通常料金の 50%。
料金改定時はここだけ直す。
"""

from __future__ import annotations

PRICES: dict[str, dict[str, float]] = {
    "claude-haiku-5-5": {"input": 0.10, "output": 0.50, "input_long": 0.50, "output_long": 2.50, "long_threshold": 100_000},
    "claude-sonnet-5-5": {"input": 2.00, "output": 10.00},
}
BATCH_DISCOUNT = 0.5
CACHE_WRITE_MULT = 1.25  # 5分 TTL のキャッシュ書き込み
CACHE_READ_MULT = 0.1


def cost_usd(model: str, input_tokens: int, output_tokens: int,
             cache_write: int = 0, cache_read: int = 0, batch: bool = False) -> float:
    key = next((k for k in PRICES if model.startswith(k) or k in model), None)
    if key is None:
        return float("nan")
    p = PRICES[key]
    prompt_total = input_tokens + cache_write + cache_read
    long = "long_threshold" in p and prompt_total > p["long_threshold"]
    pin = p["input_long"] if long else p["input"]
    pout = p["output_long"] if long else p["output"]
    c = (input_tokens * pin + cache_write * pin * CACHE_WRITE_MULT
         + cache_read * pin * CACHE_READ_MULT + output_tokens * pout) / 1_000_000
    return c * (BATCH_DISCOUNT if batch else 1.0)
