"""Phase 7 — Groq answer composition + output guard."""

from mf_compose.composer import compose_from_ask
from mf_compose.models import ChatResult, ComposeOutcome, ComposeResult
from mf_compose.pipeline import chat

__all__ = [
    "ChatResult",
    "ComposeOutcome",
    "ComposeResult",
    "chat",
    "compose_from_ask",
]
