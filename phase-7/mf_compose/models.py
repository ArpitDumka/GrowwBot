"""Phase 7 composition result models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ComposeOutcome(StrEnum):
    ANSWERED = "ANSWERED"
    REFUSED = "REFUSED"
    NOT_FOUND = "NOT_FOUND"
    ERROR = "ERROR"


@dataclass
class ComposeResult:
    outcome: ComposeOutcome
    text: str
    citation_url: str | None = None
    last_updated: str | None = None
    chunk_id: str | None = None
    model_id: str | None = None
    guard_violations: list[str] = field(default_factory=list)
    used_llm: bool = False
    log_safe: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome.value,
            "text": self.text,
            "citation_url": self.citation_url,
            "last_updated": self.last_updated,
            "chunk_id": self.chunk_id,
            "model_id": self.model_id,
            "guard_violations": self.guard_violations,
            "used_llm": self.used_llm,
            "log_safe": self.log_safe,
        }


@dataclass
class ChatResult:
    """Full stack: guard + retrieval + composition."""

    query: str
    compose: ComposeResult
    guard: Any = None
    retrieval: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "compose": self.compose.to_dict(),
            "guard": self.guard.to_dict() if hasattr(self.guard, "to_dict") else None,
            "retrieval": self.retrieval.to_dict() if hasattr(self.retrieval, "to_dict") else None,
        }
