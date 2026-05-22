"""Tests for ``mf_ingest.encoding``."""

from __future__ import annotations

from mf_ingest.encoding import decode_html_bytes


def test_utf8_roundtrip() -> None:
    raw = "<html>₹100</html>".encode("utf-8")
    text, enc = decode_html_bytes(raw)
    assert "₹" in text
    assert enc == "utf-8"
