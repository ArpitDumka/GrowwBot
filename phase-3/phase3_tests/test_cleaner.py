"""Phase 3.1 text cleaner."""

from __future__ import annotations

import pytest

from mf_clean import (
    clean_text,
    collapse_whitespace,
    compute_corpus_boilerplate_lines,
    join_split_numbers,
    normalize_boilerplate_line,
)


def test_collapse_whitespace() -> None:
    assert collapse_whitespace("a   b\n\nc\t") == "a b c"


def test_join_split_numbers() -> None:
    s = "AUM is ₹4,433.\n98 Cr for the fund."
    assert join_split_numbers(s) == "AUM is ₹4,433.98 Cr for the fund."


def test_clean_text_preserves_currency_and_percent() -> None:
    t = "Expense 0.85%  and  min  SIP  ₹100  here."
    assert clean_text(t) == "Expense 0.85% and min SIP ₹100 here."


def test_clean_text_strips_emoji() -> None:
    assert "😀" not in clean_text("NAV ₹10 🚀 growth")


def test_clean_text_strips_control_chars() -> None:
    assert "\x00" not in clean_text("safe\x00text")
    assert "\x7f" not in clean_text("x\x7fy")


def test_definition_marker_line_dropped() -> None:
    raw = "Exit load 1%.\nUnderstand terms: annualised returns are not guaranteed.\nMore facts."
    out = clean_text(raw, drop_definition_marker_lines=True)
    assert "Exit load" in out
    assert "Understand terms" not in out
    assert "annualised returns" not in out.casefold()
    assert "More facts" in out


def test_corpus_boilerplate_removed() -> None:
    common = "This is a repeated footer disclaimer line for every page."
    p1 = f"Scheme A facts.\n{common}\nMore A."
    p2 = f"Scheme B facts.\n{common}\nMore B."
    p3 = f"Scheme C.\n{common}\nTail."
    boiler = compute_corpus_boilerplate_lines([p1, p2, p3], min_fraction=0.8)
    assert normalize_boilerplate_line(common) in boiler
    c1 = clean_text(p1, corpus_boilerplate_lines=boiler)
    assert common not in c1
    assert "Scheme A facts" in c1


def test_corpus_boilerplate_not_removed_if_rare() -> None:
    pages = ["one\nUNIQUE_LINE_X\nend", "two\nother\nend", "three\nother\nend"]
    boiler = compute_corpus_boilerplate_lines(pages, min_fraction=0.8)
    assert normalize_boilerplate_line("UNIQUE_LINE_X") not in boiler


@pytest.mark.parametrize(
    "drop_defs",
    [True, False],
)
def test_clean_text_drop_definition_flag(drop_defs: bool) -> None:
    line = "Annualised returns are not indicative of future performance."
    out = clean_text(line, drop_definition_marker_lines=drop_defs)
    if drop_defs:
        assert out == ""
    else:
        assert "Annualised" in out
