from mf_guard.contextual_reply import is_contextual_short_reply, try_contextual_reply


def test_no_after_thanks_offer():
    prior_a = (
        "You're welcome! Ask anytime about HDFC Mid Cap, ELSS, Liquid, or any of the "
        "other schemes I support. What would you like to know about HDFC funds?"
    )
    r = try_contextual_reply("no", prior_user_query="thanks", prior_assistant_answer=prior_a, llm=None)
    assert r is not None
    assert "no problem" in r.text.casefold() or "understood" in r.text.casefold()
    assert r.suggested_replies


def test_yes_after_offer():
    prior_a = "What would you like to know about HDFC Mid Cap Fund or other schemes?"
    r = try_contextual_reply("yes", prior_user_query="hi", prior_assistant_answer=prior_a, llm=None)
    assert r is not None
    assert "expense ratio" in r.text.casefold() or "sample" in r.text.casefold()


def test_no_without_prior_returns_none():
    assert try_contextual_reply("no", prior_user_query=None, prior_assistant_answer=None) is None


def test_is_contextual_short_reply():
    assert is_contextual_short_reply("no")
    assert is_contextual_short_reply("Yes.")
    assert not is_contextual_short_reply("What is the NAV of HDFC Mid Cap Fund?")
