"""Reordered queries should still resolve to the right HDFC scheme."""

from mf_guard.models import Outcome
from mf_guard.pipeline import process_query
from mf_guard.scheme_field import extract_schemes_and_field


def _canonical(query: str) -> str | None:
    r = extract_schemes_and_field(query)
    return r.schemes[0].canonical if r.schemes else None


def test_small_cap_reordered():
    assert _canonical("nav for small cap mutual fund of hdfc") == "HDFC Small Cap Fund"


def test_mid_cap_possessive():
    assert _canonical("what is hdfc's mid cap fund's expense ratio") == "HDFC Mid Cap Fund"


def test_gold_reordered():
    assert _canonical("nav of gold etf fof from hdfc") == "HDFC Gold ETF FoF"


def test_silver_short():
    assert _canonical("hdfc silver scheme nav") == "HDFC Silver ETF FoF"


def test_elss_keyword():
    assert _canonical("tax saver fund of hdfc lock in") == "HDFC ELSS Tax Saver Fund"


def test_pharma_keyword():
    assert _canonical("the pharma one of hdfc") == "HDFC Pharma & Healthcare Fund"


def test_manufacturing_keyword():
    assert _canonical("hdfc's manufacturing scheme") == "HDFC Manufacturing Fund"


def test_liquid_keyword():
    assert _canonical("nav of the liquid fund by hdfc") == "HDFC Liquid Fund"


def test_no_hdfc_falls_back_to_hdfc_via_fuzzy():
    # Our corpus is HDFC-only; without an explicit AMC, fuzzy resolves to HDFC.
    # Other AMCs ("SBI Small Cap") are blocked separately by _mentions_other_amc.
    r = extract_schemes_and_field("small cap fund nav")
    assert r.schemes
    assert r.schemes[0].canonical == "HDFC Small Cap Fund"


def test_pipeline_proceeds_for_reordered_query():
    r = process_query("nav for small cap mutual fund of hdfc")
    assert r.outcome == Outcome.PROCEED
    assert r.schemes
    assert r.schemes[0].canonical == "HDFC Small Cap Fund"


def test_other_amc_with_hdfc_category_still_blocked():
    """If user mentions SBI explicitly, even with 'HDFC' in query, refuse."""
    r = process_query("compare sbi small cap with hdfc small cap")
    assert r.outcome == Outcome.REFUSE  # other AMC mentioned
