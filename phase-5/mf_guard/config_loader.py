"""Load Phase 5 YAML config files."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from mf_guard.paths import (
    ADVISORY_PATTERNS_YAML,
    CORPUS_SCOPE_YAML,
    FIELD_SYNONYMS_YAML,
    INJECTION_PATTERNS_YAML,
    PII_PATTERNS_YAML,
    QUERY_REWRITES_YAML,
)


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"config missing: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected mapping at root")
    return data


@lru_cache(maxsize=1)
def load_pii_patterns(path: Path = PII_PATTERNS_YAML) -> dict[str, list[re.Pattern[str]]]:
    raw = _read_yaml(path).get("patterns") or {}
    compiled: dict[str, list[re.Pattern[str]]] = {}
    for name, patterns in raw.items():
        if not isinstance(patterns, list):
            continue
        compiled[name] = [re.compile(p) for p in patterns if isinstance(p, str)]
    return compiled


@lru_cache(maxsize=1)
def load_injection_config(path: Path = INJECTION_PATTERNS_YAML) -> tuple[tuple[str, ...], tuple[re.Pattern[str], ...]]:
    data = _read_yaml(path)
    phrases = tuple(p.lower() for p in (data.get("phrases") or []) if isinstance(p, str))
    regexes = tuple(re.compile(r) for r in (data.get("regex") or []) if isinstance(r, str))
    return phrases, regexes


@lru_cache(maxsize=1)
def load_advisory_config(
    path: str | Path = ADVISORY_PATTERNS_YAML,
) -> tuple[tuple[str, ...], tuple[re.Pattern[str], ...]]:
    data = _read_yaml(path)
    phrases = tuple(p.lower() for p in (data.get("phrases") or []) if isinstance(p, str))
    regexes = tuple(re.compile(r) for r in (data.get("regex") or []) if isinstance(r, str))
    return phrases, regexes


@lru_cache(maxsize=1)
def load_field_synonyms(
    path: Path = FIELD_SYNONYMS_YAML,
) -> tuple[dict[str, tuple[str, ...]], tuple[str, ...], tuple[str, ...]]:
    data = _read_yaml(path)
    fields_raw = data.get("fields") or {}
    fields: dict[str, tuple[str, ...]] = {}
    for fid, syns in fields_raw.items():
        if isinstance(syns, list):
            fields[str(fid)] = tuple(s.lower() for s in syns if isinstance(s, str))
    perf = tuple(s.lower() for s in (data.get("performance_triggers") or []) if isinstance(s, str))
    unsupported = tuple(
        s.lower() for s in (data.get("unsupported_fields") or []) if isinstance(s, str)
    )
    return fields, perf, unsupported


@lru_cache(maxsize=1)
def load_corpus_out_of_scope_phrases(path: Path = CORPUS_SCOPE_YAML) -> tuple[str, ...]:
    data = _read_yaml(path)
    return tuple(
        p.lower() for p in (data.get("corpus_out_of_scope_phrases") or []) if isinstance(p, str)
    )


@lru_cache(maxsize=1)
def load_query_rewrites(path: Path = QUERY_REWRITES_YAML) -> tuple[tuple[str, str], ...]:
    data = _read_yaml(path)
    items = data.get("rewrites") or []
    pairs: list[tuple[str, str]] = []
    for row in items:
        if isinstance(row, dict) and "match" in row and "replace" in row:
            pairs.append((str(row["match"]).lower(), str(row["replace"])))
    pairs.sort(key=lambda x: len(x[0]), reverse=True)
    return tuple(pairs)
