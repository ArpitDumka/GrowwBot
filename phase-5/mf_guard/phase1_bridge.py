"""Load Phase 1 aliases + sources (same pattern as phase-4)."""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

from mf_guard.paths import PHASE1_ROOT


def ensure_phase1_on_path() -> None:
    p = str(PHASE1_ROOT.resolve())
    if p not in sys.path:
        sys.path.insert(0, p)


@lru_cache(maxsize=1)
def load_alias_registry():
    ensure_phase1_on_path()
    from ingest.aliases import load_aliases  # noqa: PLC0415

    return load_aliases()


@lru_cache(maxsize=1)
def load_source_registry():
    ensure_phase1_on_path()
    from ingest.sources import load_sources  # noqa: PLC0415

    return load_sources()


def scheme_to_source() -> dict[str, tuple[str, str]]:
    """canonical scheme name → (source_id, groww_url)."""
    reg = load_source_registry()
    return {s.scheme: (s.id, s.url) for s in reg.sources}
