"""Soft-404 detection (edge case 2.03)."""

from __future__ import annotations

import re

_SOFT_TITLE = re.compile(
    r"<title[^>]*>\s*(page not found|404|not found|error)\s*</title>",
    re.I | re.S,
)


def is_soft_404(html: str) -> bool:
    """Conservative checks to avoid false positives on valid scheme pages."""
    if _SOFT_TITLE.search(html):
        return True
    low = html.lower()
    if "page you are looking for" in low and "mutual fund" not in low[:12000]:
        return True
    return False
