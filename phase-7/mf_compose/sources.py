"""Citation URL allow-list from Phase 1 ``sources.yaml`` (§7.5)."""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

from mf_compose.paths import PHASE1_ROOT


def ensure_phase1() -> None:
    p = str(PHASE1_ROOT.resolve())
    if p not in sys.path:
        sys.path.insert(0, p)


@lru_cache(maxsize=1)
def load_allowed_urls() -> frozenset[str]:
    ensure_phase1()
    from ingest.sources import load_sources  # noqa: PLC0415

    return frozenset(s.url for s in load_sources().sources)
