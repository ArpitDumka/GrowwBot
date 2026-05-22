"""Phase 6 retrieval result models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class RetrievalOutcome(StrEnum):
    FOUND = "FOUND"
    NOT_FOUND = "NOT_FOUND"
    SKIPPED = "SKIPPED"  # guard refused or empty index


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    text: str
    scheme: str
    section: str
    source_id: str
    url: str
    last_updated: str
    fields_detected: tuple[str, ...]
    doc_type: str
    hybrid_score: float = 0.0
    boost: float = 0.0
    rerank_score: float = 0.0
    final_score: float = 0.0


@dataclass
class RetrievalResult:
    outcome: RetrievalOutcome
    message: str | None = None
    chunks: list[RetrievedChunk] = field(default_factory=list)
    low_confidence: bool = False
    groww_url: str | None = None
    field_id: str | None = None
    scheme: str | None = None
    used_header_fast_path: bool = False
    reranker_used: bool = False
    fallback_no_filter: bool = False
    log_safe: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome.value,
            "message": self.message,
            "low_confidence": self.low_confidence,
            "groww_url": self.groww_url,
            "field_id": self.field_id,
            "scheme": self.scheme,
            "used_header_fast_path": self.used_header_fast_path,
            "reranker_used": self.reranker_used,
            "chunks": [
                {
                    "chunk_id": c.chunk_id,
                    "scheme": c.scheme,
                    "section": c.section,
                    "url": c.url,
                    "final_score": c.final_score,
                    "text_preview": c.text[:200],
                }
                for c in self.chunks
            ],
            "log_safe": self.log_safe,
        }


@dataclass
class AskResult:
    """Combined Phase 5 guard + Phase 6 retrieval."""

    guard: Any
    retrieval: RetrievalResult | None = None

    def to_dict(self) -> dict[str, Any]:
        g = self.guard.to_dict() if hasattr(self.guard, "to_dict") else {}
        return {
            "guard": g,
            "retrieval": self.retrieval.to_dict() if self.retrieval else None,
        }
