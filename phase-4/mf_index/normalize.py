"""Pre-embedding text normalization (edge 4.08)."""

from __future__ import annotations

import re
import unicodedata

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def normalize_for_embedding(text: str) -> str:
    """NFKC + drop control chars; preserve ₹ and %."""
    t = unicodedata.normalize("NFKC", text)
    t = _CONTROL.sub("", t)
    return t.strip()
