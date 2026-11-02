"""埋め込みモデルの抽象化（LLMClient と同じ考え方）。実装はローカル GPU の ruri-v3 のみ。

torch / sentence-transformers は依存グループ rag に入れているので、使うときは `uv run --group rag ...`。
import は実装の中で遅延させ、書き起こし側のスクリプトが torch を読み込まないようにする。
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod

import numpy as np


class EmbeddingClient(ABC):
    model_id: str
    dim: int

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> np.ndarray:
        """文書（検索される側）を埋め込む。戻り値は L2 正規化済み float32 [n, dim]。"""

    @abstractmethod
    def embed_query(self, text: str) -> np.ndarray:
        """検索クエリを埋め込む。戻り値は L2 正規化済み float32 [dim]。"""


class RuriEmbedding(EmbeddingClient):
    """cl-nagoya/ruri-v3（Apache-2.0）。モデルカードの指定どおり、検索では接頭辞
    「検索クエリ: 」「検索文書: 」を付ける（付けないと検索精度が落ちる）。"""

    QUERY_PREFIX = "検索クエリ: "
    DOC_PREFIX = "検索文書: "

    def __init__(self, model_id: str = "cl-nagoya/ruri-v3-310m", device: str | None = None, batch_size: int = 32):
        import torch
        from sentence_transformers import SentenceTransformer

        self.model_id = model_id
        # EMBED_DEVICE=cpu で GPU があっても CPU を使う（サーバに置くときの確認用）
        self.device = device or os.environ.get("EMBED_DEVICE") or ("cuda" if torch.cuda.is_available() else "cpu")
        self.batch_size = batch_size
        self._m = SentenceTransformer(model_id, device=self.device)
        self.dim = self._m.get_sentence_embedding_dimension()

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        v = self._m.encode([self.DOC_PREFIX + t for t in texts], batch_size=self.batch_size,
                           normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
        return v.astype(np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        v = self._m.encode([self.QUERY_PREFIX + text], normalize_embeddings=True, convert_to_numpy=True)
        return v[0].astype(np.float32)


def get_embedder(name: str = "ruri-v3-310m") -> EmbeddingClient:
    if name.startswith("ruri-"):
        return RuriEmbedding(f"cl-nagoya/{name}")
    raise ValueError(f"unknown embedder: {name}")
