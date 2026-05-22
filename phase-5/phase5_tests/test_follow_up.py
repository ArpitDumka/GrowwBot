from mf_guard.follow_up import expand_follow_up, is_follow_up, resolve_follow_up_query


def test_is_follow_up_why():
    assert is_follow_up("why")
    assert is_follow_up("Why?")


def test_is_follow_up_yes_no():
    assert is_follow_up("no")
    assert is_follow_up("yes")


def test_is_follow_up_not_long_question():
    assert not is_follow_up("What is the lock-in period of HDFC ELSS Tax Saver Fund?")


def test_expand_follow_up_attaches_prior_turn():
    out = expand_follow_up(
        "why",
        prior_user_query="What is the lock-in period of HDFC ELSS Tax Saver Fund?",
        prior_assistant_answer="I couldn't find that exact fact on the Groww page.",
    )
    assert "Previous user question:" in out
    assert "HDFC ELSS" in out
    assert "Follow-up: why" in out


def test_expand_skips_without_prior():
    assert expand_follow_up("why", prior_user_query=None, prior_assistant_answer=None) == "why"


def test_resolve_field_follow_up_rewrites_question():
    prior_a = "I have factual data for HDFC Liquid Fund from its Groww scheme page."
    out = resolve_follow_up_query(
        "expense ratio",
        prior_user_query="hdfc liquid fund",
        prior_assistant_answer=prior_a,
    )
    assert out == "What is the expense ratio of HDFC Liquid Fund?"
