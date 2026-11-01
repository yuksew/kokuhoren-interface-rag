"""LLM 呼び出しの抽象。書き起こしロジックは特定ベンダーの SDK に依存しない。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class Attachment:
    """モデルに渡す添付。PDF（1ページ切り出し）または画像。"""

    kind: Literal["pdf", "png"]
    data: bytes


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0


@dataclass
class LLMResult:
    model: str
    text: str
    parsed: Any | None  # JSON をパースできた場合の値
    usage: Usage
    stop_reason: str | None
    latency_s: float
    request_id: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class BatchItemResult:
    custom_id: str
    result: LLMResult | None
    error: str | None


class LLMClient(ABC):
    """構造化出力（JSON）を返す LLM クライアント。

    バッチ処理（非同期・割安）に対応する実装は supports_batch = True にし、
    submit_batch / batch_status / batch_results を実装する。
    """

    provider: str = "abstract"
    supports_batch: bool = False

    def submit_batch(self, requests: list[tuple[str, dict[str, Any]]]) -> str:
        """[(custom_id, generate_json と同じ引数の dict), ...] を投入し、バッチ ID を返す。"""
        raise NotImplementedError

    def batch_status(self, batch_id: str) -> dict[str, Any]:
        """{"status": "in_progress" | "ended" | ..., "counts": {...}}"""
        raise NotImplementedError

    def batch_results(self, batch_id: str) -> Iterator[BatchItemResult]:
        raise NotImplementedError

    @abstractmethod
    def generate_json(
        self,
        *,
        model: str,
        system: str,
        user_text: str,
        attachments: list[Attachment],
        schema: dict[str, Any],
        max_tokens: int,
        effort: str | None = None,
    ) -> LLMResult:
        """system + 添付 + user_text を渡し、schema に従う JSON を返させる。"""
