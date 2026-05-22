"""Phase 5 — friendly deterministic replies for greetings / thanks / farewells."""

from mf_guard.intent import detect_smalltalk
from mf_guard.models import Intent, Outcome
from mf_guard.pipeline import process_query


def test_detect_greeting_short():
    assert detect_smalltalk("hi") == "greeting"
    assert detect_smalltalk("Hello") == "greeting"
    assert detect_smalltalk("Good morning") == "greeting"
    assert detect_smalltalk("Hey there!") == "greeting"
    assert detect_smalltalk("namaste") == "greeting"


def test_detect_ack():
    assert detect_smalltalk("ok") == "ack"
    assert detect_smalltalk("Okay!") == "ack"
    assert detect_smalltalk("got it") == "ack"
    assert detect_smalltalk("cool") == "appreciation"
    assert detect_smalltalk("cool thanks") is None  # mixed — not pure thanks/ack


def test_detect_thanks():
    assert detect_smalltalk("thanks") == "thanks"
    assert detect_smalltalk("Thank you") == "thanks"


def test_detect_farewell():
    assert detect_smalltalk("bye") == "farewell"
    assert detect_smalltalk("Goodbye!") == "farewell"


def test_real_question_not_smalltalk():
    """A real fund question that starts with 'Hi' must not be treated as smalltalk."""
    assert detect_smalltalk("Hi, what is the expense ratio of HDFC Mid Cap Fund?") is None
    assert detect_smalltalk("hello expense ratio of HDFC Mid Cap") is None


def test_long_query_not_smalltalk():
    assert detect_smalltalk("hi " * 30) is None


def test_pipeline_greeting_friendly_refuse():
    r = process_query("Hi, Good Morning")
    assert r.outcome == Outcome.REFUSE
    assert r.intent == Intent.SMALLTALK
    assert "Hi" in r.message
    assert "HDFC" in r.message


def test_pipeline_real_question_proceeds():
    r = process_query("What is the expense ratio of HDFC Mid Cap Fund?")
    assert r.outcome == Outcome.PROCEED


def test_pipeline_thanks_response():
    r = process_query("thank you")
    assert r.outcome == Outcome.REFUSE
    assert r.intent == Intent.SMALLTALK
    assert "welcome" in r.message.lower()


def test_pipeline_ok_ack_response():
    r = process_query("ok")
    assert r.outcome == Outcome.REFUSE
    assert r.intent == Intent.SMALLTALK
    assert r.message  # short ack, not NOT_FOUND
    assert "indexed" not in r.message.lower()
