from mf_guard import templates
from mf_guard.templates import assert_no_query_interpolation


def test_templates_static():
    for msg in (
        templates.ADVISORY,
        templates.COMPARISON,
        templates.PII,
        templates.MIXED_INTENT,
    ):
        assert "{" not in msg
        assert_no_query_interpolation(msg, "should I invest in HDFC Mid Cap Fund?")
