from mf_guard.follow_up import expand_follow_up, is_follow_up


def test_is_follow_up_why():
    assert is_follow_up("why")
    assert is_follow_up("Why?")


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
