"""Phase 5 tests — ensure phase-1 is importable."""

from __future__ import annotations

import sys
from pathlib import Path

PHASE1 = Path(__file__).resolve().parents[2] / "phase-1"
if str(PHASE1) not in sys.path:
    sys.path.insert(0, str(PHASE1))
