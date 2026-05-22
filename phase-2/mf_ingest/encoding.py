"""Decode HTML response bytes with UTF-8 first, CP1252 fallback (edge case 2.08)."""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)

_REPLACEMENT = "\ufffd"
_MOJIBAKE_HINTS = ("â‚¹", "â‚¬", "â€")


def decode_html_bytes(data: bytes) -> tuple[str, str]:
    """Return ``(text, encoding_used)``.

    Tries UTF-8, then falls back to CP1252 if UTF-8 yields replacement chars
    alongside classic mojibake for the rupee sign.
    """
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("cp1252", errors="replace")
        return text, "cp1252"

    if _REPLACEMENT in text or any(h in text for h in _MOJIBAKE_HINTS):
        alt = data.decode("cp1252", errors="replace")
        if _REPLACEMENT not in alt and "₹" in alt:
            log.warning("ENCODING_FALLBACK: used cp1252 instead of utf-8 for HTML body")
            return alt, "cp1252"

    return text, "utf-8"
