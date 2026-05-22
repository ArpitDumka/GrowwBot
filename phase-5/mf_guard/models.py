"""Data models for the Phase 5 guard pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Intent(StrEnum):
    FACT_QUERY = "FACT_QUERY"
    ADVISORY = "ADVISORY"
    PERFORMANCE = "PERFORMANCE"
    COMPARISON = "COMPARISON"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    JAILBREAK = "JAILBREAK"
    PII = "PII"
    MULTI_SCHEME = "MULTI_SCHEME"
    MIXED_INTENT = "MIXED_INTENT"
    EMPTY = "EMPTY"
    OVERSIZED = "OVERSIZED"
    UNSUPPORTED_SCRIPT = "UNSUPPORTED_SCRIPT"
    NFO = "NFO"
    SMALLTALK = "SMALLTALK"  # greetings, thanks, farewells — friendly deterministic reply


class Outcome(StrEnum):
    PROCEED = "PROCEED"
    REFUSE = "REFUSE"


@dataclass(frozen=True)
class SchemeMatch:
    canonical: str
    source_id: str
    groww_url: str
    legacy: bool = False
    fuzzy: bool = False


@dataclass
class GuardResult:
    """Output of ``process_query`` — consumed by Phase 6 retriever."""

    outcome: Outcome
    intent: Intent
    message: str | None = None
    template_id: str | None = None
    original_query: str = ""
    working_query: str = ""
    rewritten_query: str | None = None
    query_hash: str = ""
    schemes: list[SchemeMatch] = field(default_factory=list)
    field_id: str | None = None
    intents_detected: list[Intent] = field(default_factory=list)
    pii_types: list[str] = field(default_factory=list)
    truncated: bool = False
    log_safe: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome.value,
            "intent": self.intent.value,
            "message": self.message,
            "template_id": self.template_id,
            "rewritten_query": self.rewritten_query,
            "query_hash": self.query_hash,
            "schemes": [
                {
                    "canonical": s.canonical,
                    "source_id": s.source_id,
                    "groww_url": s.groww_url,
                    "legacy": s.legacy,
                    "fuzzy": s.fuzzy,
                }
                for s in self.schemes
            ],
            "field_id": self.field_id,
            "intents_detected": [i.value for i in self.intents_detected],
            "pii_types": self.pii_types,
            "truncated": self.truncated,
            "log_safe": self.log_safe,
        }
