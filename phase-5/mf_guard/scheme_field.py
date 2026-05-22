"""Phase 5.3 — scheme and field extraction."""

from __future__ import annotations

from dataclasses import dataclass

from mf_guard.config_loader import load_field_synonyms
from mf_guard.models import SchemeMatch
from mf_guard.phase1_bridge import load_alias_registry, scheme_to_source

try:
    from rapidfuzz import fuzz
except ImportError:  # pragma: no cover
    fuzz = None  # type: ignore[assignment]

_FUZZY_THRESHOLD = 85

# Category keywords -> canonical scheme name. Used when "hdfc" and a category
# token co-occur in any order, e.g. "small cap mutual fund of hdfc",
# "hdfc's pharma scheme", "the silver one from hdfc".
# Longest keys first so multi-word categories win over single tokens.
_HDFC_CATEGORY_HINTS: tuple[tuple[str, str], ...] = (
    ("pharma and healthcare", "HDFC Pharma & Healthcare Fund"),
    ("pharma & healthcare",   "HDFC Pharma & Healthcare Fund"),
    ("manufacturing fund",    "HDFC Manufacturing Fund"),
    ("manufacturing",         "HDFC Manufacturing Fund"),
    ("gold etf fof",          "HDFC Gold ETF FoF"),
    ("gold fund of fund",     "HDFC Gold ETF FoF"),
    ("gold fof",              "HDFC Gold ETF FoF"),
    ("silver etf fof",        "HDFC Silver ETF FoF"),
    ("silver fund of fund",   "HDFC Silver ETF FoF"),
    ("silver fof",            "HDFC Silver ETF FoF"),
    ("tax saver",             "HDFC ELSS Tax Saver Fund"),
    ("elss",                  "HDFC ELSS Tax Saver Fund"),
    ("defence",               "HDFC Defence Fund"),
    ("defense",               "HDFC Defence Fund"),
    ("pharma",                "HDFC Pharma & Healthcare Fund"),
    ("healthcare",            "HDFC Pharma & Healthcare Fund"),
    ("flexi cap",             "HDFC Flexi Cap Fund"),
    ("flexicap",              "HDFC Flexi Cap Fund"),
    ("flexi-cap",             "HDFC Flexi Cap Fund"),
    ("equity fund",           "HDFC Flexi Cap Fund"),  # legacy alias
    ("mid cap",               "HDFC Mid Cap Fund"),
    ("midcap",                "HDFC Mid Cap Fund"),
    ("mid-cap",               "HDFC Mid Cap Fund"),
    ("small cap",             "HDFC Small Cap Fund"),
    ("smallcap",              "HDFC Small Cap Fund"),
    ("small-cap",             "HDFC Small Cap Fund"),
    ("gold",                  "HDFC Gold ETF FoF"),
    ("silver",                "HDFC Silver ETF FoF"),
    ("liquid fund",           "HDFC Liquid Fund"),
    ("liquid",                "HDFC Liquid Fund"),
)


@dataclass(frozen=True)
class ExtractionResult:
    schemes: tuple[SchemeMatch, ...]
    field_id: str | None
    performance_field: bool
    unsupported_field: str | None


def find_schemes_in_query(query: str, registry) -> list:
    from ingest.aliases import normalize  # noqa: PLC0415

    nq = normalize(query)
    best_per_canonical: dict[str, object] = {}
    for key, match in registry._index.items():
        if not key or key not in nq:
            continue
        prev = best_per_canonical.get(match.canonical)
        if prev is None or len(key) > len(normalize(prev.surface_form)):
            best_per_canonical[match.canonical] = match
    return list(best_per_canonical.values())


def _fuzzy_match_scheme(query: str, registry):
    if fuzz is None:
        return None
    from ingest.aliases import normalize  # noqa: PLC0415
    from rapidfuzz import process  # noqa: PLC0415

    nq = normalize(query)
    keys = [k for k in registry._index if len(k) >= 8]
    hit = process.extractOne(nq, keys, scorer=fuzz.partial_ratio, score_cutoff=_FUZZY_THRESHOLD)
    if hit:
        return registry._index[hit[0]]
    return None


def _cooccurrence_match_scheme(query: str, registry):
    """Match when 'hdfc' co-occurs with a category keyword in any order.

    Handles reordered phrasings the alias list cannot enumerate:
      - "nav for small cap mutual fund of hdfc" -> HDFC Small Cap Fund
      - "hdfc's gold scheme"                    -> HDFC Gold ETF FoF
      - "tell me the manufacturing one by hdfc" -> HDFC Manufacturing Fund
    """
    from ingest.aliases import normalize  # noqa: PLC0415

    nq = normalize(query)
    if "hdfc" not in nq:
        return None
    for hint, canonical in _HDFC_CATEGORY_HINTS:
        if hint in nq:
            for _key, match in registry._index.items():
                if match.canonical == canonical:
                    return match
    return None


def extract_field(query: str) -> tuple[str | None, bool, str | None]:
    """Return (canonical_field_id, is_performance_trigger, unsupported_label)."""
    field_syns, perf_triggers, unsupported = load_field_synonyms()
    ql = query.casefold()

    for label in unsupported:
        if label in ql:
            return None, False, label

    for trigger in perf_triggers:
        if trigger in ql:
            return None, True, None

    best: tuple[int, str] | None = None
    for fid, syns in field_syns.items():
        for syn in syns:
            if syn in ql:
                if best is None or len(syn) > best[0]:
                    best = (len(syn), fid)
    return (best[1] if best else None), False, None


def extract_schemes_and_field(query: str) -> ExtractionResult:
    registry = load_alias_registry()
    mapping = scheme_to_source()
    matches = find_schemes_in_query(query, registry)

    fuzzy_used = False
    if len(matches) == 0:
        cooccur = _cooccurrence_match_scheme(query, registry)
        if cooccur:
            matches = [cooccur]
        else:
            fuzzy = _fuzzy_match_scheme(query, registry)
            if fuzzy:
                matches = [fuzzy]
                fuzzy_used = True

    schemes: list[SchemeMatch] = []
    for m in matches:
        sid, url = mapping.get(m.canonical, ("", ""))
        schemes.append(
            SchemeMatch(
                canonical=m.canonical,
                source_id=sid,
                groww_url=url,
                legacy=m.legacy,
                fuzzy=fuzzy_used,
            )
        )

    field_id, perf, unsupported = extract_field(query)
    return ExtractionResult(
        schemes=tuple(schemes),
        field_id=field_id,
        performance_field=perf,
        unsupported_field=unsupported,
    )
