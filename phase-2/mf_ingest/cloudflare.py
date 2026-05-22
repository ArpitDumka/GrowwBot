"""Cloudflare / bot-challenge sniffing (edge case 2.04)."""

from __future__ import annotations

_CHALLENGE_MARKERS = (
    "cf-chl-bypass",
    "__cf_chl_jschl_tk__",
    "cf-browser-verification",
    "Checking your browser",
    "Just a moment",
)


def is_cloudflare_challenge(html: str) -> bool:
    lower = html.lower()
    return any(m.lower() in lower for m in _CHALLENGE_MARKERS)
