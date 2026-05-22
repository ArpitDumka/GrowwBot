from mf_eval.checks import check_outcome, check_sentence_count
from mf_eval.loaders import load_tolerances
from mf_eval.models import QaCase


def test_oos_accepts_not_found():
    case = QaCase(
        id="x",
        question="q",
        expected_type="oos_wrong_amc",
        expected_outcome="REFUSED",
    )
    assert check_outcome(case, "NOT_FOUND").passed


def test_sentence_cap():
    case = QaCase(id="x", question="q", expected_type="factual", expected_outcome="ANSWERED")
    long = "One. Two. Three. Four."
    r = check_sentence_count(case, long)
    assert not r.passed
