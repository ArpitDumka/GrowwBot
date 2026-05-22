"""Phase 6 tests — path setup."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for name in ("phase-1", "phase-4", "phase-5", "phase-6"):
    p = str((ROOT / name).resolve())
    if p not in sys.path:
        sys.path.insert(0, p)
