"""Pytest bootstrap: ``phase-1`` on path for ``ingest.sources``; ``phase-2`` for ``mf_ingest``."""

from __future__ import annotations

import sys
from pathlib import Path

_PHASE2 = Path(__file__).resolve().parents[1]
_REPO = _PHASE2.parent
_PHASE1 = _REPO / "phase-1"

for p in (str(_PHASE2), str(_PHASE1)):
    if p not in sys.path:
        sys.path.insert(0, p)
