"""Eval data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

ExpectedType = Literal[
    "factual",
    "advisory",
    "performance",
    "pii",
    "oos_wrong_amc",
    "oos_non_mf",
]
MatchType = Literal["exact", "regex", "contains", "semantic"]
ExpectedOutcome = Literal["ANSWERED", "REFUSED", "NOT_FOUND", "ERROR"]


@dataclass(frozen=True)
class FieldExpectation:
    field: str
    value: float | None = None
    unit: str | None = None
    tolerance: float | None = None
    pattern: str | None = None


@dataclass(frozen=True)
class QaCase:
    id: str
    question: str
    expected_type: ExpectedType
    expected_outcome: ExpectedOutcome
    expected_url: str | None = None
    must_contain: tuple[str, ...] = ()
    must_not_contain: tuple[str, ...] = ()
    match_type: MatchType = "contains"
    last_verified: str = ""
    notes: str = ""
    expected_fields: tuple[FieldExpectation, ...] = ()
    expected_chunk_id: str | None = None
    max_sentences: int = 3
    tags: tuple[str, ...] = ()


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str = ""
    skipped: bool = False


@dataclass
class CaseResult:
    case: QaCase
    outcome: str
    answer: str
    citation_url: str | None
    latency_ms: int
    checks: list[CheckResult] = field(default_factory=list)
    trace_id: str = ""
    chunk_id: str | None = None

    @property
    def passed(self) -> bool:
        return all(c.passed or c.skipped for c in self.checks) and any(
            c.name == "overall" and c.passed for c in self.checks
        )


@dataclass
class EvalReport:
    mode: str
    total: int
    passed: int
    failed: int
    skipped_link: int
    results: list[CaseResult]
    metrics: dict[str, Any]
    targets_met: bool
