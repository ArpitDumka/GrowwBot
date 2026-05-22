"""§3.3 Groww-specific cleaning."""

from __future__ import annotations

from mf_clean.groww_clean import strip_groww_ui_noise


def test_strip_nav_substring() -> None:
    t = "NAV ₹10. Stocks / F&O / Mutual Funds More text about fund."
    out = strip_groww_ui_noise(t)
    assert "Stocks" not in out
    assert "₹10" in out


def test_drop_mega_menu_line() -> None:
    t = "Header line\nStocks | F&O | Mutual Funds\nBody about exit load 1%."
    out = strip_groww_ui_noise(t)
    assert "F&O" not in out
    assert "exit load" in out.casefold()


def test_drop_footer_line() -> None:
    t = "Facts here.\nCopyright 2026 Groww. All rights reserved."
    out = strip_groww_ui_noise(t)
    assert "Copyright" not in out
    assert "Facts here" in out


def test_understand_terms_run_removed() -> None:
    t = "Real line\nUnderstand terms: jargon\nDefinition line one\nDefinition two\n\nAfter blank"
    out = strip_groww_ui_noise(t)
    assert "Understand terms" not in out
    assert "After blank" in out
