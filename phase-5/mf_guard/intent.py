"""Phase 5.2 — rule-based intent classification."""

from __future__ import annotations

import re
import unicodedata

from mf_guard.config_loader import load_advisory_config, load_field_synonyms, load_injection_config
from mf_guard.models import Intent
from mf_guard.phase1_bridge import load_alias_registry

_URL_RE = re.compile(r"https?://[^\s]+|www\.[^\s]+", re.I)
def detect_smalltalk(query: str) -> str | None:
    """Return conversational kind for social messages, else None. See ``conversational`` module."""
    from mf_guard.conversational import classify_conversational

    return classify_conversational(query)
_COMPARISON_RE = re.compile(
    r"(?i)\b(?:lower|higher|better|worse|more|less)\s+than\b"
    r"|\bvs\.?\b|\bversus\b|\bcompared\s+to\b"
)
_NFO_RE = re.compile(r"(?i)\b(?:nfo|new\s+fund\s+offer|upcoming\s+launch|launching\s+soon)\b")
_NUMERIC_ONLY_RE = re.compile(r"^[\d\s.,%₹rs]+$", re.I)
_LATIN_RE = re.compile(r"[A-Za-z]")


def _has_non_latin_script(text: str) -> bool:
    for ch in text:
        if ch.isspace() or ch.isdigit():
            continue
        name = unicodedata.name(ch, "")
        if "LATIN" in name:
            continue
        cat = unicodedata.category(ch)
        if cat.startswith("L"):
            return True
    return False


def count_distinct_schemes(query: str, registry) -> int:
    from ingest.aliases import normalize  # noqa: PLC0415

    nq = normalize(query)
    return len({m.canonical for key, m in registry._index.items() if key and key in nq})


def detect_performance_intent(query: str) -> bool:
    _, perf_triggers, _ = load_field_synonyms()
    q = query.casefold()
    return any(t in q for t in perf_triggers)


def detect_comparison_intent(query: str, n_schemes: int) -> bool:
    if _COMPARISON_RE.search(query):
        return True
    if n_schemes >= 2 and re.search(r"(?i)\bor\b", query):
        return True
    return False


def has_factual_substance(query: str, n_schemes: int) -> bool:
    """True when query also asks a factual scheme/field question (edge 5.10)."""
    if n_schemes >= 1:
        field_syns, _, _ = load_field_synonyms()
        ql = query.casefold()
        if any(any(syn in ql for syn in syns) for syns in field_syns.values()):
            return True
        if re.search(r"(?i)\b(?:what|how much|minimum|tell me)\b", query):
            return True
    return False


def classify_intents(query: str) -> list[Intent]:
    q = query.strip()
    ql = q.casefold()
    labels: list[Intent] = []

    if not q:
        return [Intent.EMPTY]

    if _has_non_latin_script(q) and not _LATIN_RE.search(q):
        return [Intent.UNSUPPORTED_SCRIPT]

    if len(q) > 2000:
        labels.append(Intent.OVERSIZED)

    inj_phrases, inj_regex = load_injection_config()
    if any(p in ql for p in inj_phrases) or any(r.search(q) for r in inj_regex):
        labels.append(Intent.JAILBREAK)

    adv_phrases, adv_regex = load_advisory_config()
    advisory = any(p in ql for p in adv_phrases) or any(r.search(q) for r in adv_regex)
    if advisory:
        labels.append(Intent.ADVISORY)

    if _URL_RE.search(q):
        labels.append(Intent.OUT_OF_SCOPE)

    if _NUMERIC_ONLY_RE.match(q):
        labels.append(Intent.OUT_OF_SCOPE)

    if _NFO_RE.search(q):
        labels.append(Intent.OUT_OF_SCOPE)
        labels.append(Intent.NFO)

    registry = load_alias_registry()
    n_schemes = count_distinct_schemes(q, registry)

    if detect_comparison_intent(q, n_schemes):
        labels.append(Intent.COMPARISON)

    if detect_performance_intent(q):
        labels.append(Intent.PERFORMANCE)

    if n_schemes > 1:
        labels.append(Intent.MULTI_SCHEME)

    if advisory and (
        has_factual_substance(q, n_schemes)
        or "also" in ql
        or Intent.PERFORMANCE in labels
        or Intent.COMPARISON in labels
    ):
        labels.append(Intent.MIXED_INTENT)

    if not labels or labels == [Intent.OVERSIZED]:
        labels.append(Intent.FACT_QUERY)

    return list(dict.fromkeys(labels))
