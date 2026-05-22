"""Detect vague / scheme-label-only queries (no factual field asked)."""

from __future__ import annotations

import re

# If none of these appear, the user likely only named a scheme (e.g. "hdfc mid cap fund").
_QUESTION_MARKERS = re.compile(
    r"\b("
    r"what|how|when|where|why|which|tell|show|give|explain|"
    r"minimum|min|expense|nav|exit|load|lock|benchmark|risk|riskometer|"
    r"aum|sip|lumpsum|tax|stamp|holding|manager|objective|"
    r"ratio|period|classification|index|download|statement"
    r")\b",
    re.I,
)


def is_scheme_only_query(query: str) -> bool:
    """True when the query names a scheme but does not ask a specific fact."""
    q = query.strip()
    if len(q) < 3:
        return False
    return _QUESTION_MARKERS.search(q) is None
