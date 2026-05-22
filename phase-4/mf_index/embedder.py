"""Embedder interface + BGE default (architecture §4.1)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

import numpy as np

from mf_index.normalize import normalize_for_embedding
from mf_index.paths import DEFAULT_MODEL_ID

BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


@runtime_checkable
class Embedder(Protocol):
    @property
    def model_id(self) -> str: ...

    @property
    def dimension(self) -> int: ...

    def embed_documents(self, texts: list[str]) -> np.ndarray: ...

    def embed_query(self, text: str) -> np.ndarray: ...


class BaseEmbedder(ABC):
    @property
    @abstractmethod
    def model_id(self) -> str: ...

    @property
    @abstractmethod
    def dimension(self) -> int: ...

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> np.ndarray: ...

    def embed_query(self, text: str) -> np.ndarray:
        return self.embed_documents([text])[0]


class BGEEmbedder(BaseEmbedder):
    """``BAAI/bge-small-en-v1.5`` via sentence-transformers (384-d)."""

    def __init__(self, model_id: str = DEFAULT_MODEL_ID) -> None:
        from sentence_transformers import SentenceTransformer

        self._model_id = model_id
        self._model = SentenceTransformer(model_id)

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def dimension(self) -> int:
        getter = getattr(self._model, "get_embedding_dimension", None) or getattr(
            self._model, "get_sentence_embedding_dimension", None
        )
        dim = getter() if getter else None
        if dim is None:
            raise RuntimeError("could not determine embedding dimension")
        return int(dim)

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dimension), dtype=np.float32)
        normed = [normalize_for_embedding(t) for t in texts]
        for i, t in enumerate(normed):
            if not t:
                raise ValueError(f"empty text at index {i} (edge 4.09)")
        vecs = self._model.encode(
            normed,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return np.asarray(vecs, dtype=np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        q = normalize_for_embedding(text)
        if not q:
            raise ValueError("empty query text (edge 4.09)")
        prefixed = BGE_QUERY_PREFIX + q
        vec = self._model.encode(
            [prefixed],
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return np.asarray(vec[0], dtype=np.float32)


class HashingEmbedder(BaseEmbedder):
    """Deterministic low-dim embedder for unit tests (no HF download)."""

    def __init__(self, dimension: int = 384, model_id: str = "test/hashing") -> None:
        self._dim = dimension
        self._model_id = model_id

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        import hashlib

        out = np.zeros((len(texts), self._dim), dtype=np.float32)
        for i, t in enumerate(texts):
            normed = normalize_for_embedding(t)
            if not normed:
                raise ValueError(f"empty text at index {i}")
            h = hashlib.sha256(normed.encode("utf-8")).digest()
            for j in range(self._dim):
                out[i, j] = (h[j % len(h)] / 255.0) * 2 - 1
            norm = np.linalg.norm(out[i])
            if norm > 0:
                out[i] /= norm
        return out


def create_embedder(model_id: str | None = None, *, test: bool = False) -> Embedder:
    if test:
        return HashingEmbedder(model_id="test/hashing")
    return BGEEmbedder(model_id or DEFAULT_MODEL_ID)
