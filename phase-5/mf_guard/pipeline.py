"""Phase 5 — full pre-retrieval guard pipeline (§5.1)."""

from __future__ import annotations

from mf_guard import templates
from mf_guard.config_loader import load_corpus_out_of_scope_phrases
from mf_guard.conversational import classify_conversational, conversational_response
from mf_guard.intent import (
    classify_intents,
    count_distinct_schemes,
    detect_performance_intent,
)
from mf_guard.models import GuardResult, Intent, Outcome, SchemeMatch
from mf_guard.paths import MAX_QUERY_CHARS, TRUNCATE_TO_CHARS
from mf_guard.phase1_bridge import load_alias_registry
from mf_guard.pii import detect_pii, query_hash, scrub_for_log
from mf_guard.rewriter import rewrite_query
from mf_guard.scheme_field import extract_schemes_and_field
from mf_guard.templates import assert_no_query_interpolation


def _refuse(
    intent: Intent,
    message: str,
    template_id: str,
    *,
    original: str,
    working: str,
    intents: list[Intent],
    pii_types: tuple[str, ...] = (),
    schemes: list[SchemeMatch] | None = None,
    truncated: bool = False,
) -> GuardResult:
    assert_no_query_interpolation(message, original)
    h = query_hash(working)
    return GuardResult(
        outcome=Outcome.REFUSE,
        intent=intent,
        message=message,
        template_id=template_id,
        original_query=original,
        working_query=working,
        query_hash=h,
        schemes=schemes or [],
        intents_detected=intents,
        pii_types=list(pii_types),
        truncated=truncated,
        log_safe={"query_hash": h, "intent": intent.value, "outcome": Outcome.REFUSE.value},
    )


def _proceed(
    *,
    original: str,
    working: str,
    rewritten: str,
    schemes: list[SchemeMatch],
    field_id: str | None,
    intents: list[Intent],
    truncated: bool,
) -> GuardResult:
    h = query_hash(rewritten)
    return GuardResult(
        outcome=Outcome.PROCEED,
        intent=Intent.FACT_QUERY,
        original_query=original,
        working_query=working,
        rewritten_query=rewritten,
        query_hash=h,
        schemes=schemes,
        field_id=field_id,
        intents_detected=intents,
        truncated=truncated,
        log_safe={
            "query_hash": h,
            "intent": Intent.FACT_QUERY.value,
            "outcome": Outcome.PROCEED.value,
            "scheme": schemes[0].canonical if schemes else None,
            "field_id": field_id,
            "scrubbed_preview": scrub_for_log(rewritten)[:120],
        },
    )


def process_query(query: str) -> GuardResult:
    """Run PII → intent → scheme/field → rewrite. Main Phase 5 entrypoint."""
    original = query
    working = query.strip()
    truncated = False

    if not working:
        msg = templates.EMPTY
        return _refuse(Intent.EMPTY, msg, "EMPTY", original=original, working=working, intents=[Intent.EMPTY])

    if len(working) > MAX_QUERY_CHARS:
        working = working[:TRUNCATE_TO_CHARS]
        truncated = True

    # PII before conversational routing (never store or process sensitive identifiers).
    pii = detect_pii(working)
    if pii.detected:
        msg = templates.PII
        return _refuse(
            Intent.PII,
            msg,
            "PII",
            original=original,
            working=working,
            intents=[Intent.PII],
            pii_types=pii.types,
            truncated=truncated,
        )

    # Conversational / small talk — before retrieval and NOT_FOUND fallbacks.
    conv_kind = classify_conversational(working)
    if conv_kind:
        return _refuse(
            Intent.SMALLTALK,
            conversational_response(conv_kind),
            "SMALLTALK",
            original=original,
            working=working,
            intents=[Intent.SMALLTALK],
            truncated=truncated,
        )

    intents = classify_intents(working)
    registry = load_alias_registry()
    n_schemes = count_distinct_schemes(working, registry)
    extraction = extract_schemes_and_field(working)
    groww_url = extraction.schemes[0].groww_url if extraction.schemes else None

    def refuse(intent: Intent, msg: str, tid: str) -> GuardResult:
        return _refuse(
            intent,
            msg,
            tid,
            original=original,
            working=working,
            intents=intents,
            schemes=list(extraction.schemes),
            truncated=truncated,
        )

    if Intent.UNSUPPORTED_SCRIPT in intents:
        return refuse(Intent.UNSUPPORTED_SCRIPT, templates.UNSUPPORTED_SCRIPT, "UNSUPPORTED_SCRIPT")

    if Intent.JAILBREAK in intents:
        return refuse(Intent.JAILBREAK, templates.JAILBREAK, "JAILBREAK")

    if Intent.MIXED_INTENT in intents:
        return refuse(Intent.MIXED_INTENT, templates.MIXED_INTENT, "MIXED_INTENT")

    if Intent.ADVISORY in intents:
        return refuse(Intent.ADVISORY, templates.ADVISORY, "ADVISORY")

    if Intent.COMPARISON in intents:
        msg = templates.comparison_message(groww_url)
        return refuse(Intent.COMPARISON, msg, "COMPARISON")

    if Intent.MULTI_SCHEME in intents:
        return refuse(Intent.MULTI_SCHEME, templates.MULTI_SCHEME, "MULTI_SCHEME")

    if Intent.PERFORMANCE in intents or extraction.performance_field:
        msg = templates.performance_message(groww_url)
        return refuse(Intent.PERFORMANCE, msg, "PERFORMANCE")

    if Intent.NFO in intents:
        return refuse(Intent.OUT_OF_SCOPE, templates.NFO, "NFO")

    if _is_document_download_topic(working):
        return refuse(Intent.OUT_OF_SCOPE, templates.DOCUMENT_DOWNLOAD, "DOCUMENT_DOWNLOAD")

    if Intent.OUT_OF_SCOPE in intents:
        if _numeric_only(working):
            return refuse(Intent.OUT_OF_SCOPE, templates.NUMERIC_ONLY, "NUMERIC_ONLY")
        return refuse(Intent.OUT_OF_SCOPE, templates.OUT_OF_SCOPE, "OUT_OF_SCOPE")

    # Reject any query that mentions another AMC, even if a fuzzy HDFC scheme also matches
    # (architecture: only the 10 HDFC schemes are in scope).
    if _mentions_other_amc(working):
        return refuse(Intent.OUT_OF_SCOPE, templates.UNKNOWN_SCHEME, "UNKNOWN_SCHEME")

    if not extraction.schemes and _looks_like_unknown(working):
        return refuse(Intent.OUT_OF_SCOPE, templates.UNKNOWN_SCHEME, "UNKNOWN_SCHEME")

    rewritten = rewrite_query(working)
    schemes = list(extraction.schemes)

    return _proceed(
        original=original,
        working=working,
        rewritten=rewritten,
        schemes=schemes,
        field_id=extraction.field_id,
        intents=intents,
        truncated=truncated,
    )


def _looks_like_unknown(query: str) -> bool:
    ql = query.casefold()
    return "hdfc" in ql or "mutual fund" in ql


_OTHER_AMC_RE = __import__("re").compile(
    r"(?i)\b(?:sbi|icici(?:\s*prudential)?|axis|nippon(?:\s*india)?|kotak|"
    r"aditya\s*birla|uti|tata|ppfas|parag\s*parikh|motilal(?:\s*oswal)?|mirae(?:\s*asset)?|"
    r"dsp|franklin(?:\s*templeton)?|invesco|edelweiss|quant(?:\s+mutual)?|bandhan|"
    r"baroda|canara(?:\s*robeco)?|sundaram|jm\s+financial|navi|whiteoak|"
    r"l&t|lic|ppfas|samco|360\s*one|helios)\b"
)


def _mentions_other_amc(query: str) -> bool:
    """True when the query mentions a non-HDFC AMC (out of corpus)."""
    return bool(_OTHER_AMC_RE.search(query))


def _numeric_only(query: str) -> bool:
    import re

    return bool(re.match(r"^[\d\s.,%₹rs]+$", query.strip(), re.I))


def _is_document_download_topic(query: str) -> bool:
    ql = query.casefold()
    return any(p in ql for p in load_corpus_out_of_scope_phrases())
