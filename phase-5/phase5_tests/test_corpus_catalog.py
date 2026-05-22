from mf_guard.corpus_catalog import (
    build_field_question,
    is_all_funds_field_query,
    is_field_only_follow_up,
    is_list_corpus_query,
    scheme_from_prior_turn,
    try_build_field_question,
    try_corpus_catalog_reply,
)


def test_scheme_from_assistant_hint():
    prior_a = "I have factual data for HDFC Liquid Fund from its Groww scheme page."
    assert scheme_from_prior_turn("hdfc liquid fund", prior_a) == "HDFC Liquid Fund"


def test_build_field_question_after_scheme_turn():
    prior_a = "I have factual data for HDFC Liquid Fund from its Groww scheme page."
    built = try_build_field_question(
        "expense ratio",
        prior_user_query="hdfc liquid fund",
        prior_assistant_answer=prior_a,
    )
    assert built == "What is the expense ratio of HDFC Liquid Fund?"


def test_list_ten_funds():
    r = try_corpus_catalog_reply("list those 10")
    assert r is not None
    assert "HDFC Liquid Fund" in r.text
    assert "HDFC Mid Cap Fund" in r.text
    assert r.text.count("\n") >= 9


def test_all_funds_expense_ratio():
    assert is_all_funds_field_query("expense ratio for all funds")
    r = try_corpus_catalog_reply("expense ratio for all funds")
    assert r is not None
    assert "HDFC Mid Cap Fund" in r.text
    assert "%" in r.text


def test_is_field_only():
    assert is_field_only_follow_up("expense ratio")
    assert not is_field_only_follow_up("What is the expense ratio of HDFC Mid Cap Fund?")


def test_build_field_question_helper():
    assert (
        build_field_question("x", "HDFC Liquid Fund", "expense_ratio")
        == "What is the expense ratio of HDFC Liquid Fund?"
    )
