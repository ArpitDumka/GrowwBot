from mf_guard.models import Outcome
from mf_guard.pipeline import process_query


def test_factual_proceeds():
    r = process_query("What is the expense ratio of HDFC Mid Cap Fund?")
    assert r.outcome == Outcome.PROCEED
    assert r.schemes
    assert r.schemes[0].canonical == "HDFC Mid Cap Fund"
    assert r.field_id == "expense_ratio"
    assert r.rewritten_query


def test_hinglish_proceeds():
    r = process_query("HDFC mid cap ka expense ratio kya hai?")
    assert r.outcome == Outcome.PROCEED
    assert r.schemes[0].canonical == "HDFC Mid Cap Fund"


def test_elss_rewrite():
    r = process_query("What is the ELSS lock-in for HDFC ELSS?")
    assert r.outcome == Outcome.PROCEED
    assert "lock in period" in (r.rewritten_query or "").casefold()


def test_fuzzy_typo():
    r = process_query("exit load for HDFC Mdcap fund")
    assert r.outcome == Outcome.PROCEED
    assert r.schemes[0].canonical == "HDFC Mid Cap Fund"
    assert r.schemes[0].fuzzy is True


def test_oversized_truncates_but_proceeds():
    q = "What is the expense ratio of HDFC Mid Cap Fund? " + ("x" * 2500)
    r = process_query(q)
    assert r.truncated
    assert r.outcome == Outcome.PROCEED
