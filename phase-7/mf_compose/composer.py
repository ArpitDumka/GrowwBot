"""§7 — compose answers from retrieval results."""

from __future__ import annotations

from mf_compose.groq_client import GroqLLMClient, LLMClient
from mf_compose.llm_config import GroqLLMConfig, load_llm_config
from mf_compose.models import ComposeOutcome, ComposeResult
from mf_compose.output_guard import GuardContext, apply_output_guard, apply_smalltalk_guard
from mf_compose.prompts import build_messages, build_smalltalk_messages
from mf_compose.sources import load_allowed_urls

_SCHEME_ONLY_HINT = (
    "What would you like to know? For example: expense ratio, latest NAV, minimum SIP, "
    "exit load, lock-in period (for ELSS), risk level, or benchmark."
)


def compose_from_ask(
    ask_result,
    *,
    llm: LLMClient | None = None,
    llm_cfg: GroqLLMConfig | None = None,
) -> ComposeResult:
    """Build final user-facing text from Phase 6 ``AskResult``."""
    from mf_guard.models import Outcome as GuardOutcome  # noqa: PLC0415
    from mf_retrieve.models import RetrievalOutcome  # noqa: PLC0415

    from mf_guard.models import Intent as GuardIntent  # noqa: PLC0415

    cfg = llm_cfg or load_llm_config()
    guard = ask_result.guard

    if guard.intent == GuardIntent.SMALLTALK:
        return _compose_smalltalk(guard, llm=llm, cfg=cfg)

    if guard.outcome != GuardOutcome.PROCEED:
        return ComposeResult(
            outcome=ComposeOutcome.REFUSED,
            text=guard.message or "",
            used_llm=False,
            log_safe={"source": "guard", "intent": guard.intent.value},
        )

    retrieval = ask_result.retrieval
    if not retrieval:
        return ComposeResult(
            outcome=ComposeOutcome.NOT_FOUND,
            text="No retrieval result.",
            used_llm=False,
        )

    if retrieval.outcome != RetrievalOutcome.FOUND or not retrieval.chunks:
        from mf_guard.conversational import (  # noqa: PLC0415
            classify_conversational,
            conversational_response,
            looks_like_fund_question,
        )

        query = guard.rewritten_query or guard.working_query
        conv = classify_conversational(query)
        if conv and not looks_like_fund_question(query):
            return ComposeResult(
                outcome=ComposeOutcome.ANSWERED,
                text=conversational_response(conv),
                used_llm=False,
                log_safe={"source": "conversational_fallback", "kind": conv},
            )
        return ComposeResult(
            outcome=ComposeOutcome.NOT_FOUND,
            text=retrieval.message or "I could not find an answer.",
            citation_url=retrieval.groww_url,
            used_llm=False,
            log_safe={"source": "retrieval"},
        )

    chunk = retrieval.chunks[0]
    query = guard.rewritten_query or guard.working_query

    from mf_retrieve.query_shape import is_scheme_only_query  # noqa: PLC0415

    if is_scheme_only_query(query) and retrieval.log_safe.get("fast_path") == "scheme_overview":
        body = (
            f"I have factual data for {chunk.scheme} from its Groww scheme page. "
            f"{_SCHEME_ONLY_HINT}"
        )
        footer_date = chunk.last_updated
        text = f"{body}\nSource: {chunk.url}\nLast updated from sources: {footer_date}"
        return ComposeResult(
            outcome=ComposeOutcome.ANSWERED,
            text=text,
            citation_url=chunk.url,
            last_updated=footer_date,
            chunk_id=chunk.chunk_id,
            used_llm=False,
            log_safe={"source": "scheme_only_hint", "chunk_id": chunk.chunk_id},
        )

    messages = build_messages(
        query,
        chunk_text=chunk.text,
        source_url=chunk.url,
        last_updated=chunk.last_updated,
    )

    client = llm or GroqLLMClient()
    try:
        raw = client.complete(messages, cfg=cfg)
    except Exception as e:
        return ComposeResult(
            outcome=ComposeOutcome.ERROR,
            text="The service is temporarily unavailable. Please try again shortly.",
            used_llm=False,
            log_safe={"error": str(e)[:200]},
        )

    gctx = GuardContext(
        chunk_text=chunk.text,
        citation_url=chunk.url,
        last_updated=chunk.last_updated,
        allowed_urls=load_allowed_urls(),
    )
    final, violations = apply_output_guard(raw, gctx)

    return ComposeResult(
        outcome=ComposeOutcome.ANSWERED,
        text=final,
        citation_url=chunk.url,
        last_updated=chunk.last_updated,
        chunk_id=chunk.chunk_id,
        model_id=cfg.model_id,
        guard_violations=violations,
        used_llm=True,
        log_safe={
            "chunk_id": chunk.chunk_id,
            "violations": violations,
            "query_hash": guard.query_hash,
        },
    )


def _compose_smalltalk(
    guard,
    *,
    llm: LLMClient | None,
    cfg: GroqLLMConfig,
) -> ComposeResult:
    """Friendly reply for greetings / thanks / ack — LLM when available, else Phase 5 template."""
    fallback = (guard.message or "").strip()
    if not fallback:
        from mf_guard.conversational import conversational_response  # noqa: PLC0415

        fallback = conversational_response("greeting")
    query = (guard.working_query or "").strip()

    client = llm or GroqLLMClient()
    messages = build_smalltalk_messages(query)
    try:
        raw = client.complete(messages, cfg=cfg)
        cleaned, violations = apply_smalltalk_guard(raw)
        if cleaned:
            return ComposeResult(
                outcome=ComposeOutcome.ANSWERED,
                text=cleaned,
                model_id=cfg.model_id,
                used_llm=True,
                guard_violations=violations,
                log_safe={"source": "conversational_llm", "query_hash": guard.query_hash},
            )
    except Exception as e:
        return ComposeResult(
            outcome=ComposeOutcome.ANSWERED,
            text=fallback,
            used_llm=False,
            log_safe={"source": "conversational_fallback", "error": str(e)[:200]},
        )

    return ComposeResult(
        outcome=ComposeOutcome.ANSWERED,
        text=fallback,
        used_llm=False,
        log_safe={"source": "conversational_template", "query_hash": guard.query_hash},
    )
