"""Put ``phase-3`` on ``sys.path`` for ``mf_clean`` imports."""

from __future__ import annotations

import sys
from pathlib import Path

_PHASE3 = Path(__file__).resolve().parents[1]
if str(_PHASE3) not in sys.path:
    sys.path.insert(0, str(_PHASE3))
