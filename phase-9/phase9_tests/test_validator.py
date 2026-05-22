from mf_eval.validator import validate_coverage


def test_qa_set_coverage():
    errors = validate_coverage()
    assert errors == [], errors
