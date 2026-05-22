"""Phase 5.4 — deterministic query rewriting."""

from __future__ import annotations

import re

from mf_guard.config_loader import load_query_rewrites

_WS_RE = re.compile(r"\s+")


def rewrite_query(query: str) -> str:
    """Expand abbreviations and normalize whitespace."""
    q = query.strip()
    ql = q.casefold()
    for match, replace in load_query_rewrites():
        if match in ql:
            pattern = re.compile(re.escape(match), re.I)
            q = pattern.sub(replace, q)
            ql = q.casefold()
    return _WS_RE.sub(" ", q).strip()
