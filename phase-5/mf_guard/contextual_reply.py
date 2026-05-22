"""Short contextual replies (yes / no / ok) using the previous chat turn."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

_POLARITY_RE = re.compile(
    r"^(?:"
    r"yes|yeah|yep|yup|sure|ok|okay|please|alright|absolutely|correct|right|"
    r"no|nope|nah|not really|no thanks|no thank you|thanks|thank you|thx"
    r")(?:[.!?,\s]+)*$",
    re.I,
)

_OFFER_MORE = (
    "what would you like",
    "ask me about",
    "ask about any",
    "pick a sample",
    "try a sample",
    "when you're ready",
    "feel free to ask",
    "ask anytime",
    "ask another",
    "another factual",
    "sample question",
)
_THANKS_TAIL = ("you're welcome", "youre welcome", "glad that helped", "happy to help")
_FACT_MARKERS = ("source:", "last updated from sources:", "groww.in/mutual-funds")

_MAX_PRIOR_USER = 500
_MAX_PRIOR_ASSISTANT = 600

Polarity = Literal["yes", "no", "thanks", "neutral"]


@dataclass(frozen=True)
class ContextualReplyResult:
    text: str
    suggested_replies: tuple[str, ...] = ()
    used_llm: bool = False


def is_contextual_short_reply(query: str) -> bool:
    q = query.strip()
    if not q or len(q) > 40:
        return False
    return bool(_POLARITY_RE.match(q))


def _polarity(query: str) -> Polarity | None:
    s = query.strip().casefold().rstrip(".,!? ")
    if s in {"no", "nope", "nah", "not really", "no thanks", "no thank you"}:
        return "no"
    if s in {"thanks", "thank you", "thx"}:
        return "thanks"
    if s in {
        "yes", "yeah", "yep", "yup", "sure", "ok", "okay", "please",
        "alright", "absolutely", "correct", "right",
    }:
        return "yes"
    if s in {"ok", "okay", "got it", "cool", "fine"}:
        return "neutral"
    return None


def _prior_intent(assistant: str) -> Literal["offer", "thanks", "fact", "other"]:
    a = assistant.casefold()
    if any(m in a for m in _FACT_MARKERS):
        return "fact"
    if any(t in a for t in _THANKS_TAIL):
        return "thanks"
    if any(o in a for o in _OFFER_MORE):
        return "offer"
    return "other"


def _deterministic_reply(
    polarity: Polarity,
    intent: Literal["offer", "thanks", "fact", "other"],
) -> ContextualReplyResult:
    if polarity == "no":
        if intent in {"offer", "thanks", "other"}:
            return ContextualReplyResult(
                "No problem. I'm here whenever you need factual answers about the 10 HDFC "
                "schemes on Groww. Ask a new question anytime, or say hi if you'd like ideas.",
                suggested_replies=("What is the expense ratio of HDFC Mid Cap Fund?", "Hi"),
            )
        return ContextualReplyResult(
            "Understood. If you'd like another fact on the same fund or a different HDFC scheme, "
            "just ask — for example exit load, minimum SIP, or lock-in for ELSS.",
            suggested_replies=(
                "What is the minimum SIP for HDFC Liquid Fund?",
                "What is the lock-in period of HDFC ELSS Tax Saver Fund?",
            ),
        )

    if polarity == "thanks":
        return ContextualReplyResult(
            "You're welcome! Ask anytime about HDFC Mid Cap, ELSS, Liquid, or any of the "
            "other schemes I support.",
            suggested_replies=("What is the exit load on HDFC Defence Fund?", "No thanks"),
        )

    if polarity == "yes":
        if intent == "fact":
            return ContextualReplyResult(
                "Glad that helped. What else would you like to know about that fund or "
                "another HDFC scheme?",
                suggested_replies=(
                    "What is the expense ratio of HDFC Mid Cap Fund?",
                    "What is the minimum SIP for HDFC Liquid Fund?",
                ),
            )
        return ContextualReplyResult(
            "Great — pick a sample question below, or ask something specific, e.g. "
            "\"What is the expense ratio of HDFC Mid Cap Fund?\" or "
            "\"What is the minimum SIP for HDFC Liquid Fund?\"",
            suggested_replies=(
                "What is the expense ratio of HDFC Mid Cap Fund?",
                "What is the minimum SIP for HDFC Liquid Fund?",
            ),
        )

    # neutral ack
    return ContextualReplyResult(
        "Sounds good. Ask me about any HDFC scheme when you're ready — expense ratio, "
        "exit load, minimum SIP, lock-in (ELSS), NAV, or benchmark.",
        suggested_replies=(
            "What is the latest NAV of HDFC Small Cap Fund?",
            "What is the exit load on HDFC ELSS Tax Saver Fund?",
        ),
    )


def try_contextual_reply(
    query: str,
    *,
    prior_user_query: str | None,
    prior_assistant_answer: str | None,
    llm: object | None = None,
) -> ContextualReplyResult | None:
    """Return a conversational answer for yes/no/ok when prior turn exists."""
    q = query.strip()
    if not prior_assistant_answer or not is_contextual_short_reply(q):
        return None

    polarity = _polarity(q)
    if polarity is None:
        return None

    prior_a = prior_assistant_answer.strip()[:_MAX_PRIOR_ASSISTANT]
    prior_u = (prior_user_query or "").strip()[:_MAX_PRIOR_USER]
    intent = _prior_intent(prior_a)
    fallback = _deterministic_reply(polarity, intent)

    if llm is None:
        return fallback

    try:
        from mf_compose.groq_client import GroqLLMClient  # noqa: PLC0415
        from mf_compose.llm_config import load_llm_config  # noqa: PLC0415
        from mf_compose.output_guard import apply_smalltalk_guard  # noqa: PLC0415
        from mf_compose.prompts import build_contextual_messages  # noqa: PLC0415

        cfg = load_llm_config()
        client = llm if hasattr(llm, "complete") else GroqLLMClient()
        messages = build_contextual_messages(
            q,
            prior_user=prior_u,
            prior_assistant=prior_a,
            polarity=polarity,
        )
        raw = client.complete(messages, cfg=cfg)
        cleaned, _violations = apply_smalltalk_guard(raw)
        if cleaned:
            return ContextualReplyResult(
                cleaned,
                suggested_replies=fallback.suggested_replies,
                used_llm=True,
            )
    except Exception:
        pass

    return fallback
