"""Expand short follow-up messages using prior turn context."""

from __future__ import annotations

import re

_FOLLOW_UP_START = re.compile(
    r"^(?:why|how come|how so|explain|clarify|what do you mean|elaborate|tell me more|"
    r"can you explain|what about that|and that|so)\b",
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
    # Very short non-question fragments after a fund turn (e.g. "why?", "explain").
    return len(q.split()) <= 4 and q.endswith("?")


def expand_follow_up(
    query: str,
    *,
    prior_user_query: str | None,
    prior_assistant_answer: str | None,
) -> str:
    """Attach previous Q/A so scheme + field resolution work on 'why' / 'explain'."""
    q = query.strip()
    if not prior_user_query or not is_follow_up(q):
        return q
    prev_q = prior_user_query.strip()[:_MAX_PRIOR_USER]
    prev_a = (prior_assistant_answer or "").strip()[:_MAX_PRIOR_ASSISTANT]
    if prev_a:
        return (
            f"Previous user question: {prev_q}\n"
            f"Previous assistant answer: {prev_a}\n"
            f"Follow-up: {q}"
        )
    return f"Previous user question: {prev_q}\nFollow-up: {q}"
