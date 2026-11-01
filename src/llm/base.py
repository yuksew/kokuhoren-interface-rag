"""LLM 呼び出しの抽象。書き起こしロジックは特定ベンダーの SDK に依存しない。"""

from __future__ import annotations

from abc import ABC, abstractmethod
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


class LLMClient(ABC):
    """構造化出力（JSON）を返す LLM クライアント。"""

    provider: str = "abstract"

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
