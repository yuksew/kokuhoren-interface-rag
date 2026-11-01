from .base import Attachment, LLMClient, LLMResult, Usage


def get_client(provider: str) -> LLMClient:
    if provider == "anthropic":
        from .anthropic_client import AnthropicClient

        return AnthropicClient()
    if provider == "mock":
        from .mock_client import MockClient

        return MockClient()
    raise ValueError(f"unknown provider: {provider}")


__all__ = ["Attachment", "LLMClient", "LLMResult", "Usage", "get_client"]
