"""Anthropic（Claude API）実装。API キーは環境変数 ANTHROPIC_API_KEY から SDK が読む。"""

from __future__ import annotations

import base64
import json
import time
from collections.abc import Iterator
from typing import Any

import anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

from .base import Attachment, BatchItemResult, LLMClient, LLMResult, Usage


class AnthropicClient(LLMClient):
    provider = "anthropic"
    supports_batch = True

    def __init__(self, max_retries: int = 4, timeout_s: float = 900.0) -> None:
        # 認証情報は SDK の既定の解決順（ANTHROPIC_API_KEY など）に任せる
        self._client = anthropic.Anthropic(max_retries=max_retries, timeout=timeout_s)

    @staticmethod
    def _block(att: Attachment) -> dict[str, Any]:
        b64 = base64.standard_b64encode(att.data).decode("ascii")
        if att.kind == "pdf":
            return {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": b64}}
        return {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b64}}

    def build_params(
        self,
        *,
        model: str,
        system: str,
        user_text: str,
        attachments: list[Attachment],
        schema: dict[str, Any],
        max_tokens: int,
        effort: str | None = None,
    ) -> dict[str, Any]:
        """Messages API のリクエスト本体。Batch API でも同じものを params として使う。"""
        output_config: dict[str, Any] = {"format": {"type": "json_schema", "schema": schema}}
        if effort:
            output_config["effort"] = effort
        content = [self._block(a) for a in attachments] + [{"type": "text", "text": user_text}]
        return {
            "model": model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": content}],
            "output_config": output_config,
        }

    @staticmethod
    def _to_result(msg: Any, latency: float) -> LLMResult:
        text = "".join(b.text for b in msg.content if b.type == "text")
        parsed = None
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            pass
        u = msg.usage
        usage = Usage(
            input_tokens=u.input_tokens or 0,
            output_tokens=u.output_tokens or 0,
            cache_creation_input_tokens=getattr(u, "cache_creation_input_tokens", 0) or 0,
            cache_read_input_tokens=getattr(u, "cache_read_input_tokens", 0) or 0,
        )
        stop_details = getattr(msg, "stop_details", None)
        return LLMResult(
            model=msg.model,
            text=text,
            parsed=parsed,
            usage=usage,
            stop_reason=msg.stop_reason,
            latency_s=latency,
            request_id=getattr(msg, "_request_id", None),
            raw={"stop_details": stop_details.to_dict() if stop_details else None},
        )

    def generate_json(self, **kw: Any) -> LLMResult:
        params = self.build_params(**kw)
        t0 = time.monotonic()
        # 出力が長くなり得るのでストリーミングで受けて最終メッセージを得る
        with self._client.messages.stream(**params) as stream:
            msg = stream.get_final_message()
        return self._to_result(msg, time.monotonic() - t0)

    # ---- Batch API（料金 50%。非同期、通常 1 時間以内・最大 24 時間） ----
    def submit_batch(self, requests: list[tuple[str, dict[str, Any]]]) -> str:
        reqs = [Request(custom_id=cid, params=MessageCreateParamsNonStreaming(**self.build_params(**kw)))
                for cid, kw in requests]
        return self._client.messages.batches.create(requests=reqs).id

    def batch_status(self, batch_id: str) -> dict[str, Any]:
        b = self._client.messages.batches.retrieve(batch_id)
        return {"status": b.processing_status, "counts": b.request_counts.to_dict()}

    def batch_results(self, batch_id: str) -> Iterator[BatchItemResult]:
        for r in self._client.messages.batches.results(batch_id):
            if r.result.type == "succeeded":
                yield BatchItemResult(r.custom_id, self._to_result(r.result.message, 0.0), None)
            else:
                err = getattr(r.result, "error", None)
                yield BatchItemResult(r.custom_id, None, f"{r.result.type}: {err.to_dict() if err else ''}")
