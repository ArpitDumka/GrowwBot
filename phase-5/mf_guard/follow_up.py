"""Expand short follow-up messages using prior turn context."""

from __future__ import annotations

import re

_FOLLOW_UP_START = re.compile(
    r"^(?:why|how come|how so|explain|clarify|what do you mean|elaborate|tell me more|"
    r"can you explain|what about that|and that|so)\b",
    re.I,
)
_SHORT_REPLY = re.compile(
    r"^(?:yes|yeah|yep|yup|sure|no|nope|nah|ok|okay|please|alright|absolutely|"
    r"correct|right|not really|no thanks|no thank you|thanks|thank you|thx)(?:[.!?,\s]*)$",
    re.I,
)
_MAX_PRIOR_USER = 500
_MAX_PRIOR_ASSISTANT = 600


def is_follow_up(query: str) -> bool:
    q = query.strip()
    if not q or len(q) > 80:
        return False
    if _FOLLOW_UP_START.match(q):
        return True
    if _SHORT_REPLY.match(q):
        return True
    from mf_guard.corpus_catalog import (  # noqa: PLC0415
        is_all_funds_field_query,
        is_field_only_follow_up,
        is_list_corpus_query,
    )

    if is_list_corpus_query(q) or is_all_funds_field_query(q):
        return True
    if is_field_only_follow_up(q):
        return True
    # Very short non-question fragments after a fund turn (e.g. "why?", "explain").
    return len(q.split()) <= 4 and q.endswith("?")


def resolve_follow_up_query(
    query: str,
    *,
    prior_user_query: str | None,
    prior_assistant_answer: str | None,
) -> str:
    """Rewrite follow-ups into a full question or attach prior Q/A for the guard."""
    q = query.strip()
    if not prior_user_query and not prior_assistant_answer:
        return q

    from mf_guard.corpus_catalog import try_build_field_question  # noqa: PLC0415

    built = try_build_field_question(
        q,
        prior_user_query=prior_user_query,
        prior_assistant_answer=prior_assistant_answer,
    )
    if built:
        return built

    if not is_follow_up(q):
        return q

    prev_q = (prior_user_query or "").strip()[:_MAX_PRIOR_USER]
    prev_a = (prior_assistant_answer or "").strip()[:_MAX_PRIOR_ASSISTANT]
    if prev_a:
        return (
            f"Previous user question: {prev_q}\n"
            f"Previous assistant answer: {prev_a}\n"
            f"Follow-up: {q}"
        )
    return f"Previous user question: {prev_q}\nFollow-up: {q}"


def expand_follow_up(
    query: str,
    *,
    prior_user_query: str | None,
    prior_assistant_answer: str | None,
) -> str:
    """Backward-compatible alias."""
    return resolve_follow_up_query(
        query,
        prior_user_query=prior_user_query,
        prior_assistant_answer=prior_assistant_answer,
    )
