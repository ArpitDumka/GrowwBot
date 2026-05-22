"""Conversational intent detection and deterministic replies (pre-retrieval).

Runs before RAG / NOT_FOUND fallbacks so casual chat never gets scheme-miss messages.
"""

from __future__ import annotations

import re
from typing import Literal

ConversationalKind = Literal["greeting", "help", "thanks", "farewell", "ack", "appreciation", "casual"]

_MAX_LEN = 80
_MAX_TOKENS = 10
_PUNCT_TAIL_RE = re.compile(r"[!?.,;:\s\-—]+$")

_FUND_KEYWORDS = (
    "fund", "hdfc", "sip", "nav", "expense", "ratio", "exit", "load",
    "lock", "benchmark", "scheme", "amc", "mutual", "elss", "folio",
    "dividend", "ter", "aum", "isin", "groww", "invest", "redemption",
)

_GREETING_WORDS = frozenset({
    "hi", "hii", "hiii", "hey", "heyy", "hello", "helo", "hola", "howdy", "yo", "sup",
    "namaste", "namaskar", "greetings", "salaam", "salam", "welcome",
})
_GREETING_PHRASES = (
    "good morning", "good afternoon", "good evening", "good night",
    "how are you", "how r u", "how do you do", "whats up", "what's up", "how's it going",
)

_HELP_PHRASES = (
    "help", "help me", "i need help", "what can you do", "what do you do",
    "who are you", "what are you", "what's your purpose", "tell me about yourself",
    "about you", "how does this work", "how to use",
)

_THANKS_WORDS = frozenset({
    "thanks", "thank", "thx", "ty", "thankyou", "dhanyavaad", "shukriya",
})
_THANKS_PHRASES = ("thank you", "thanks a lot", "many thanks", "you're welcome", "youre welcome")

_FAREWELL_WORDS = frozenset({"bye", "goodbye", "cya", "tata", "alvida"})
_FAREWELL_PHRASES = ("see you", "see ya", "take care", "good bye", "goodbye for now")

_ACK_WORDS = frozenset({"ok", "okay", "k", "kk", "sure", "yep", "yeah", "yea", "ya", "alright", "done"})
_ACK_PHRASES = ("got it", "sounds good", "that's fine", "thats fine", "all good", "noted", "understood")

_APPRECIATION_WORDS = frozenset({
    "cool", "nice", "great", "awesome", "perfect", "lovely", "wonderful", "fine", "good",
})
_CASUAL_WORDS = frozenset({"lol", "lmao", "haha", "hehe", "hmm", "hm", "wow", "omg", "idk"})

_RESPONSES: dict[ConversationalKind, str] = {
    "greeting": (
        "Hi! I'm your HDFC mutual fund facts assistant on Groww. "
        "I cover 10 schemes and answer from official Groww pages only — no investment advice. "
        "Pick a sample question below, or ask something like "
        "\"What is the expense ratio of HDFC Mid Cap Fund?\""
    ),
    "help": (
        "I answer factual questions about 10 HDFC mutual funds on Groww — things like expense ratio, "
        "exit load, minimum SIP, lock-in (ELSS), NAV, benchmark, and risk. "
        "Tap a sample question to get started, or type your own in plain English."
    ),
    "thanks": (
        "You're welcome! Ask anytime about HDFC Mid Cap, ELSS, Liquid, or any of the other "
        "schemes I support."
    ),
    "farewell": "Bye! Come back whenever you need scheme facts from Groww.",
    "ack": "Sounds good. Ask me about any HDFC scheme when you're ready.",
    "appreciation": "Glad that helped! Feel free to ask another factual question.",
    "casual": (
        "I'm here for HDFC mutual fund facts from Groww — try a sample question or ask "
        "about expense ratio, exit load, or minimum SIP for a specific fund."
    ),
}


def looks_like_fund_question(query: str) -> bool:
    """True when the message plausibly asks about schemes/facts (NOT_FOUND allowed)."""
    q = query.strip().casefold()
    if not q:
        return False
    if any(k in q for k in _FUND_KEYWORDS):
        return True
    if re.search(r"\?", q):
        return len(q) > 3
    if re.search(
        r"(?i)\b(?:what|how much|how many|when|where|which|minimum|maximum|tell me|show me|is there)\b",
        q,
    ):
        return True
    return len(q.split()) >= 5


def classify_conversational(query: str) -> ConversationalKind | None:
    """Classify short social messages. Returns None if retrieval/fallback should run."""
    q = query.strip()
    if not q or len(q) > _MAX_LEN:
        return None
    stripped = _PUNCT_TAIL_RE.sub("", q).strip().casefold()
    if not stripped:
        return None
    if looks_like_fund_question(q):
        return None

    tokens = [t for t in re.split(r"[\s,!?\-]+", stripped) if t]
    if not tokens or len(tokens) > _MAX_TOKENS:
        return None

    for phrase in _FAREWELL_PHRASES:
        if _phrase_match(stripped, phrase):
            return "farewell"
    if stripped in _FAREWELL_WORDS or any(t in _FAREWELL_WORDS for t in tokens):
        return "farewell"

    for phrase in _THANKS_PHRASES:
        if _phrase_match(stripped, phrase):
            return "thanks"
    _thanks_extra = frozenset({"you", "a", "lot", "so", "very", "much"})
    if stripped in _THANKS_WORDS or (
        tokens and all(t in _THANKS_WORDS | _thanks_extra for t in tokens)
    ):
        return "thanks"

    for phrase in _HELP_PHRASES:
        if _phrase_match(stripped, phrase):
            return "help"

    for phrase in _GREETING_PHRASES:
        if _phrase_match(stripped, phrase):
            return "greeting"
    if any(t in _GREETING_WORDS for t in tokens):
        return "greeting"

    for phrase in _ACK_PHRASES:
        if _phrase_match(stripped, phrase):
            return "ack"
    if stripped in _ACK_WORDS or (len(tokens) <= 2 and all(t in _ACK_WORDS for t in tokens)):
        return "ack"

    if stripped in _APPRECIATION_WORDS or (len(tokens) <= 2 and all(t in _APPRECIATION_WORDS for t in tokens)):
        return "appreciation"

    if stripped in _CASUAL_WORDS or stripped == "?" or (
        len(tokens) <= 2 and all(t in _CASUAL_WORDS for t in tokens)
    ):
        return "casual"

    return None


def conversational_response(kind: ConversationalKind | str) -> str:
    return _RESPONSES.get(kind, _RESPONSES["greeting"])  # type: ignore[arg-type]


def detect_smalltalk(query: str) -> str | None:
    """Backward-compatible alias used by ``intent.py`` and tests."""
    return classify_conversational(query)


def _phrase_match(stripped: str, phrase: str) -> bool:
    return (
        stripped == phrase
        or stripped.startswith(phrase + " ")
        or stripped.endswith(" " + phrase)
    )
