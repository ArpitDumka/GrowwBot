"""Load YAML config and QA set."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from mf_eval.models import FieldExpectation, QaCase
from mf_eval.paths import QA_SET_YAML, SOURCES_YAML, TARGETS_YAML, TOLERANCES_YAML


@dataclass(frozen=True)
class ToleranceConfig:
    fields: dict[str, dict[str, Any]]
    max_days_since_verified: int
    link_timeout: float
    link_retries: int
    link_soft_fail: bool


@dataclass(frozen=True)
class TargetConfig:
    metrics: dict[str, float]
    ci_metrics: dict[str, float]


def _parse_case(raw: dict) -> QaCase:
    fields: list[FieldExpectation] = []
    for name, spec in (raw.get("expected_fields") or {}).items():
        if isinstance(spec, dict):
            fields.append(
                FieldExpectation(
                    field=str(name),
                    value=float(spec["value"]) if spec.get("value") is not None else None,
                    unit=spec.get("unit"),
                    tolerance=float(spec["tolerance"]) if spec.get("tolerance") is not None else None,
                    pattern=spec.get("pattern"),
                )
            )
        elif isinstance(spec, str):
            fields.append(FieldExpectation(field=str(name), pattern=spec))

    must = raw.get("must_contain") or []
    must_not = raw.get("must_not_contain") or []
    tags = raw.get("tags") or []

    return QaCase(
        id=str(raw["id"]),
        question=str(raw["question"]),
        expected_type=raw["expected_type"],
        expected_outcome=raw.get("expected_outcome", "ANSWERED"),
        expected_url=raw.get("expected_url"),
        must_contain=tuple(str(x) for x in must),
        must_not_contain=tuple(str(x) for x in must_not),
        match_type=raw.get("match_type", "contains"),
        last_verified=str(raw.get("last_verified", "")),
        notes=str(raw.get("notes", "")),
        expected_fields=tuple(fields),
        expected_chunk_id=raw.get("expected_chunk_id"),
        max_sentences=int(raw.get("max_sentences", 3)),
        tags=tuple(str(t) for t in tags),
    )


def load_qa_set(path: Path = QA_SET_YAML) -> list[QaCase]:
    if not path.is_file():
        raise FileNotFoundError(f"qa_set.yaml not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    cases = raw.get("cases") or []
    return [_parse_case(c) for c in cases if isinstance(c, dict)]


@lru_cache(maxsize=1)
def load_tolerances(path: Path = TOLERANCES_YAML) -> ToleranceConfig:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    stale = raw.get("staleness") or {}
    link = raw.get("link_check") or {}
    return ToleranceConfig(
        fields=dict(raw.get("fields") or {}),
        max_days_since_verified=int(stale.get("max_days_since_verified", 120)),
        link_timeout=float(link.get("timeout_seconds", 30)),
        link_retries=int(link.get("retries", 1)),
        link_soft_fail=bool(link.get("soft_fail", True)),
    )


@lru_cache(maxsize=1)
def load_targets(path: Path = TARGETS_YAML, *, ci_mode: bool = False) -> TargetConfig:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    base = dict(raw.get("metrics") or {})
    if ci_mode:
        base.update(raw.get("ci_mode") or {})
    return TargetConfig(metrics={k: float(v) for k, v in base.items()}, ci_metrics=dict(raw.get("ci_mode") or {}))


def load_source_ids(path: Path = SOURCES_YAML) -> frozenset[str]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return frozenset(
        str(s["id"]) for s in raw.get("sources") or [] if isinstance(s, dict) and s.get("id")
    )


def parse_verified_date(s: str) -> date | None:
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except ValueError:
        return None
