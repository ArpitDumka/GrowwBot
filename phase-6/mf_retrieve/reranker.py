"""§6.1 [D] cross-encoder reranking."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import numpy as np

log = logging.getLogger(__name__)


class BaseReranker(ABC):
    @property
    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def score(self, query: str, passages: list[str]) -> list[float]: ...


class BGEReranker(BaseReranker):
    """``BAAI/bge-reranker-base`` via sentence-transformers CrossEncoder."""

    def __init__(self, model_id: str) -> None:
        self._model_id = model_id
        self._model = None
        self._error: str | None = None
        try:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(model_id)
        except Exception as e:  # pragma: no cover
            self._error = str(e)
            log.warning("reranker unavailable: %s", e)

    @property
    def is_available(self) -> bool:
        return self._model is not None

    def score(self, query: str, passages: list[str]) -> list[float]:
        if not self._model or not passages:
            return [0.0] * len(passages)
        pairs = [[query, p] for p in passages]
        raw = self._model.predict(pairs)
        arr = np.asarray(raw, dtype=np.float64).reshape(-1)
        # Map to 0–1 via sigmoid for stable τ comparison
        return [float(1.0 / (1.0 + np.exp(-x))) for x in arr]


class PassthroughReranker(BaseReranker):
    """Uses pre-rerank scores normalized to 0–1 (tests / reranker-down)."""

    def __init__(self, pre_scores: list[float]) -> None:
        self._pre = pre_scores

    @property
    def is_available(self) -> bool:
        return True

    def score(self, query: str, passages: list[str]) -> list[float]:
        if not self._pre:
            return [0.5] * len(passages)
        lo, hi = min(self._pre), max(self._pre)
        if hi <= lo:
            return [0.8 if s > 0 else 0.2 for s in self._pre]
        return [(s - lo) / (hi - lo) for s in self._pre]


def create_reranker(model_id: str, *, test: bool = False) -> BaseReranker:
    """When ``test=True``, caller should use ``passthrough_rerank`` in ``retrieve()``."""
    if test:
        return PassthroughReranker([])
    return BGEReranker(model_id)
