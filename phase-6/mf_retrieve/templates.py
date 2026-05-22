"""Deterministic NOT_FOUND template (§6.2)."""

from __future__ import annotations

NOT_FOUND_PREFIX = (
    "I couldn't find that exact fact on the Groww page for this scheme. "
    "You can double-check on the official scheme page: "
)

NOT_FOUND_NO_SCHEME = (
    "I'm not sure which HDFC scheme you mean. Please name a fund from the 10 I cover — "
    "for example: \"What is the expense ratio of HDFC Mid Cap Fund?\" or "
    "\"What is the minimum SIP for HDFC Liquid Fund?\""
)


def not_found_message(groww_url: str | None) -> str:
    if groww_url:
        return NOT_FOUND_PREFIX + groww_url
    return NOT_FOUND_NO_SCHEME
