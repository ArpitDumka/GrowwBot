"""Conversational intent + NOT_FOUND guard behavior."""

from mf_guard.conversational import (
    classify_conversational,
    conversational_response,
    looks_like_fund_question,
)
from mf_guard.models import Intent, Outcome
from mf_guard.pipeline import process_query


def test_casual_messages():
    assert classify_conversational("ok") == "ack"
    assert classify_conversational("cool") == "appreciation"
    assert classify_conversational("lol") == "casual"
    assert classify_conversational("hmm") == "casual"
    assert classify_conversational("thanks") == "thanks"
    assert classify_conversational("bye") == "farewell"
    assert classify_conversational("hi") == "greeting"
    assert classify_conversational("good morning") == "greeting"
    assert classify_conversational("welcome") == "greeting"
    assert classify_conversational("help") == "help"


def test_fund_question_not_conversational():
    assert classify_conversational("What is the expense ratio of HDFC Mid Cap Fund?") is None
    assert classify_conversational("hello expense ratio of HDFC Mid Cap") is None
    assert looks_like_fund_question("HDFC ELSS exit load") is True


def test_mixed_ack_not_conversational():
    assert classify_conversational("cool thanks") is None


def test_responses_human_tone():
    assert "welcome" in conversational_response("thanks").lower()
    assert "ready" in conversational_response("ack").lower() or "good" in conversational_response("ack").lower()
    assert "Glad" in conversational_response("appreciation")


def test_pipeline_ok_not_not_found():
    r = process_query("ok")
    assert r.intent == Intent.SMALLTALK
    assert r.outcome == Outcome.REFUSE
    assert "indexed" not in (r.message or "").lower()
    assert "scheme pages" not in (r.message or "").lower()


def test_pipeline_pii_before_smalltalk():
    r = process_query("ok my PAN is ABCDE1234F")
    assert r.intent == Intent.PII
