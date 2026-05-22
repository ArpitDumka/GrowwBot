"""Load valid ``source_id`` values from Phase 1 registry (edge 4.12)."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

from mf_index.paths import PHASE1_ROOT, SOURCES_YAML


def ensure_phase1_on_sys_path() -> None:
    p = str(PHASE1_ROOT.resolve())
    if p not in sys.path:
        sys.path.insert(0, p)


def load_registry_source_ids(path: Path = SOURCES_YAML) -> frozenset[str]:
    ensure_phase1_on_sys_path()
    try:
        from ingest.sources import load_sources  # noqa: PLC0415

        return frozenset(s.id for s in load_sources(path))
    except ImportError:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        items = raw.get("sources") or []
        return frozenset(str(x["id"]) for x in items if isinstance(x, dict) and "id" in x)
