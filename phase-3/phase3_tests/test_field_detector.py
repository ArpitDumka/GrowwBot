"""§3.5 field detector — canonical ids, edges 3.09 / 3.15."""

from __future__ import annotations

from mf_clean.field_detector import (
    CANONICAL_FIELD_IDS,
    detect_fields,
    list_canonical_field_ids,
    validate_fields_detected,
)


def test_canonical_field_ids_count_and_stability() -> None:
    assert len(CANONICAL_FIELD_IDS) == 15
    assert set(list_canonical_field_ids()) == CANONICAL_FIELD_IDS


def test_validate_fields_detected_filters_unknown() -> None:
    assert validate_fields_detected(["exit_load", "bogus", "tax"]) == ["exit_load", "tax"]


def test_expense_ratio_requires_percent_not_definition() -> None:
    defn = "Expense ratio is the annual fee charged by the fund house."
    assert "expense_ratio" not in detect_fields(defn, section="header", category="Mid Cap")
    body = "Total expense ratio 0.45% p.a. as on 1 Jan 2026."
    assert "expense_ratio" in detect_fields(body, section="header", category="Mid Cap")


def test_nav_rupee_or_percent_near_keyword() -> None:
    assert "nav" in detect_fields("NAV ₹42.15 as on date.", section="header", category="Mid Cap")
    assert "nav" not in detect_fields("Net asset value is the per-unit price.", section="header", category="Mid Cap")


def test_lock_in_only_for_elss_category() -> None:
    text = "ELSS 3-year lock-in applies to this investment."
    assert "lock_in" not in detect_fields(text, section="lock_in_banner", category="Mid Cap")
    assert "lock_in" in detect_fields(text, section="lock_in_banner", category="ELSS")


def test_category_none_allows_lock_in_heuristic() -> None:
    """When category is unknown, do not apply ELSS-only gate."""
    text = "3-year lock-in period."
    tags = detect_fields(text, section="header", category=None)
    assert "lock_in" in tags


def test_holdings_section_injects_holdings_tag() -> None:
    t = "Only sector labels here; no holding keyword."
    assert "holdings" in detect_fields(t, section="holdings", category="Mid Cap")
