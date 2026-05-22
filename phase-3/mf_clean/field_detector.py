"""Lightweight regex field tagging (architecture §3.5).

Tags chunks with facts the retriever can boost on. Canonical ids (exactly
these 15)::

    expense_ratio, exit_load, min_sip, min_lumpsum, lock_in, risk, benchmark,
    nav, aum, fund_manager, inception_date, objective, holdings, tax, stamp_duty

Edge-case refinements (see ``docs/edge-cases/phase-3-chunking.md``):

- **3.15** — ``expense_ratio`` requires a **numeric %** near the match, not
  definition-only prose. ``nav`` requires a **rupee amount or %** near the
  keyword, with the same definition guard.
- **3.09** — ``lock_in`` is emitted only when ``category == "ELSS"`` (scheme
  metadata trumps incidental banner or prose on other categories).
"""

from __future__ import annotations

import re
from collections.abc import Sequence

# --- Architecture §3.5 (exact set) ---
CANONICAL_FIELD_IDS: frozenset[str] = frozenset(
    {
        "expense_ratio",
        "exit_load",
        "min_sip",
        "min_lumpsum",
        "lock_in",
        "risk",
        "benchmark",
        "nav",
        "aum",
        "fund_manager",
        "inception_date",
        "objective",
        "holdings",
        "tax",
        "stamp_duty",
    }
)

_DEFINITION_NEAR = re.compile(
    r"\b(?:is|are|means|refers to|defined as)\s+(?:the|a)\b",
    re.I,
)

# Value-shaped: digits with optional decimals then %
_VALUE_PCT = re.compile(r"\d+(?:[.,]\d+)?\s*%")

# Within N chars after keyword start, require a % value (edge 3.15 ~20 chars)
_NEAR_WINDOW = 28


def _keyword_with_numeric_percent(text: str, keyword: re.Pattern[str]) -> bool:
    """True if ``keyword`` matches and a ``…%`` value appears soon after (not pure definition)."""
    for m in keyword.finditer(text):
        window = text[m.start() : m.start() + _NEAR_WINDOW]
        if _DEFINITION_NEAR.search(window[:40]):
            continue
        if _VALUE_PCT.search(window):
            return True
    return False


_NAV_VALUE = re.compile(
    r"(?:₹|rs\.?)\s*[\d,.]+|\d+(?:[.,]\d+)?\s*%",
    re.I,
)


def _nav_keyword_with_value(text: str) -> bool:
    """NAV tag when a rupee amount or % appears near the keyword (edge 3.15-style, not definitions)."""
    for m in _NAV_KW.finditer(text):
        window = text[m.start() : m.start() + _NEAR_WINDOW]
        if _DEFINITION_NEAR.search(window[:40]):
            continue
        if _NAV_VALUE.search(window):
            return True
    return False


_EXPENSE_KW = re.compile(r"expense\s+ratio|total\s+expense\s+ratio|\bter\b", re.I)
_EXPENSE_LABEL_VALUE = re.compile(
    r"expense\s+ratio\s*\(direct\)\s*:\s*[\d.,]+\s*%|expense\s+ratio\s*[\d.,]+\s*%",
    re.I,
)
_NAV_KW = re.compile(r"\bnav\b|net\s+asset\s+value", re.I)

_SIMPLE: list[tuple[str, re.Pattern[str]]] = [
    ("exit_load", re.compile(r"exit\s+load", re.I)),
    ("stamp_duty", re.compile(r"stamp\s+duty", re.I)),
    ("tax", re.compile(r"\btax\b|taxed|stcg|ltcg|capital\s+gains", re.I)),
    ("min_sip", re.compile(r"min\.?\s*(?:for\s*)?sip|minimum\s+sip", re.I)),
    ("min_lumpsum", re.compile(r"lumpsum|lump\s+sum|minimum\s+(?:lumpsum|investment)", re.I)),
    ("lock_in", re.compile(r"lock-?in|lock\s+in|\belss\b", re.I)),
    ("risk", re.compile(r"\brisk\b|riskometer|very\s+high|moderate|low\s+risk|high\s+risk", re.I)),
    ("benchmark", re.compile(r"benchmark|nifty|sensex|bse\s+\d+|tri\b", re.I)),
    (
        "aum",
        re.compile(
            r"\baum\b|fund\s+size|assets?\s+under\s+management|"
            r"(?:₹|rs\.?)\s*[\d,.]+\s*(?:cr|lakh|lac|crore)\b",
            re.I,
        ),
    ),
    ("fund_manager", re.compile(r"fund\s+manager|fund\s+management|managed\s+by", re.I)),
    ("inception_date", re.compile(r"inception|launch\s+date|since\s+\d{4}", re.I)),
    ("objective", re.compile(r"objective|investment\s+objective|about\s+the\s+fund", re.I)),
    ("holdings", re.compile(r"holding|portfolio|top\s+holding|equity\s*\d+\.\d{2}\s*%", re.I)),
]


def list_canonical_field_ids() -> list[str]:
    """Sorted list of §3.5 field ids (stable for docs / tests)."""
    return sorted(CANONICAL_FIELD_IDS)


def validate_fields_detected(tags: Sequence[str]) -> list[str]:
    """Keep only ids in :data:`CANONICAL_FIELD_IDS`, sorted unique."""
    return sorted({t for t in tags if t in CANONICAL_FIELD_IDS})


def detect_fields(
    text: str,
    *,
    section: str,
    category: str | None = None,
) -> list[str]:
    """Return sorted unique field tags implied by ``text`` (subset of §3.5)."""
    found: list[str] = []

    if _EXPENSE_LABEL_VALUE.search(text) or _keyword_with_numeric_percent(text, _EXPENSE_KW):
        found.append("expense_ratio")
    if _nav_keyword_with_value(text):
        found.append("nav")

    for field_id, pat in _SIMPLE:
        if pat.search(text):
            found.append(field_id)

    if section == "holdings" and "holdings" not in found:
        found.append("holdings")

    # Edge 3.09: lock_in only when scheme category is ELSS.
    if category is not None and category.casefold() != "elss":
        found = [f for f in found if f != "lock_in"]

    return validate_fields_detected(found)
