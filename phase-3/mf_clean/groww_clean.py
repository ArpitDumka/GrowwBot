"""Groww-specific cleaning (architecture §3.3).

Runs **before** :func:`mf_clean.cleaner.clean_text` (§3.1) in the chunk pipeline:

- Drop mega-menu style lines (``Stocks / F&O / Mutual Funds`` and similar).
- Drop short footer / legal boilerplate lines.
- Remove ``Understand terms`` definition runs (complements §3.1 line denylist).
- Substring removal for common nav snippets leaked into extracted text.

Does **not** re-parse HTML; operates on Phase 2 section strings only.
"""

from __future__ import annotations

import re

# --- Substring removals (nav / app chrome leaked into trafilatura text) ---
_NAV_SUBSTRINGS: tuple[str, ...] = (
    "Stocks/F&O/Mutual Funds",
    "Stocks / F&O / Mutual Funds",
    "Stocks|F&O|Mutual Funds",
    "Stocks | F&O | Mutual Funds",
    "Stocks·F&O·Mutual Funds",
    "Invest in Stocks",
    "Invest in Mutual Funds",
    "Search mutual funds",
    "Download the App",
    "Get the Groww App",
)

_MENU_PART = re.compile(
    r"^\s*(?:stocks|f&o|f\&o|mutual funds|ipo|etf|gold|fd|crypto|us stocks|invest|futures)\s*$",
    re.I,
)

_FOOTER_LINE = re.compile(
    r"^\s*(?:©|copyright|all rights reserved|privacy policy|terms of use|cookie policy|"
    r"sebi registration|investor charter)\b",
    re.I,
)

_UNDERSTAND_HEAD = re.compile(r"^\s*understand terms\b", re.I)


def _is_mega_menu_line(line: str) -> bool:
    """True if the line looks like a Groww top-nav crumb row (§3.3)."""
    s = line.strip()
    if len(s) < 8 or len(s) > 200:
        return False
    if not re.search(r"[|/•·]", s):
        return False
    parts = re.split(r"[|/•·]+", s)
    parts = [p.strip() for p in parts if p.strip()]
    if len(parts) < 2:
        return False
    return all(_MENU_PART.match(p) for p in parts)


def _strip_nav_substrings(text: str) -> str:
    t = text
    for needle in _NAV_SUBSTRINGS:
        t = re.sub(re.escape(needle), " ", t, flags=re.I)
    return t


def _drop_understand_terms_runs(lines: list[str]) -> list[str]:
    """Remove a ``Understand terms`` line and following glossary lines until a break."""
    out: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if _UNDERSTAND_HEAD.match(line):
            i += 1
            count = 0
            while i < n and count < 30:
                if not lines[i].strip():
                    i += 1
                    break
                i += 1
                count += 1
            continue
        out.append(line)
        i += 1
    return out


def strip_groww_ui_noise(text: str) -> str:
    """Apply §3.3 Groww-specific removals; output may still contain newlines."""
    t = _strip_nav_substrings(text)
    lines = t.splitlines()
    lines = _drop_understand_terms_runs(lines)
    kept: list[str] = []
    for line in lines:
        if _is_mega_menu_line(line):
            continue
        s = line.strip()
        if s and len(s) < 120 and _FOOTER_LINE.match(s):
            continue
        kept.append(line)
    return "\n".join(kept)
