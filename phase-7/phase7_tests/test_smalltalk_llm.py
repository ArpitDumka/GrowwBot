"""Phase 7 — conversational composer (LLM + template fallback)."""

from mf_compose.composer import compose_from_ask
from mf_compose.groq_client import StubLLMClient
from mf_compose.models import ComposeOutcome
from mf_compose.output_guard import apply_smalltalk_guard
from mf_guard.conversational import classify_conversational, conversational_response


class _Ask:
    def __init__(self, guard):
        self.guard = guard
        self.retrieval = None


class _Guard:
    def __init__(self, query, *, intent, outcome, message=""):
        self.working_query = query
        self.rewritten_query = None
        self.intent = intent
        self.outcome = outcome
        self.message = message
        self.query_hash = "qh"
        self.schemes = []


def _make_smalltalk(query: str):
    from mf_guard.models import Intent, Outcome

    kind = classify_conversational(query) or "greeting"
    msg = conversational_response(kind)
    return _Ask(_Guard(query, intent=Intent.SMALLTALK, outcome=Outcome.REFUSE, message=msg))


def test_smalltalk_llm_when_stub_provides_clean_reply():
    llm = StubLLMClient(
        "Hello! Ask me about expense ratio or exit load for any of the 10 HDFC schemes on Groww."
    )
    r = compose_from_ask(_make_smalltalk("hi"), llm=llm)
    assert r.outcome == ComposeOutcome.ANSWERED
    assert r.used_llm is True
    assert "HDFC" in r.text
    assert r.citation_url is None


def test_smalltalk_falls_back_to_template_on_guard_block():
    llm = StubLLMClient("You should invest in SBI Bluechip for better returns.")
    r = compose_from_ask(_make_smalltalk("hi"), llm=llm)
    assert r.outcome == ComposeOutcome.ANSWERED
    assert r.used_llm is False
    assert "HDFC" in r.text or "Groww" in r.text


def test_smalltalk_ok_uses_template():
    r = compose_from_ask(_make_smalltalk("ok"))
    assert r.outcome == ComposeOutcome.ANSWERED
    assert "indexed" not in r.text.lower()


def test_smalltalk_guard_unit():
    cleaned, viol = apply_smalltalk_guard("Hi there! Ask me about HDFC funds.")
    assert cleaned
    assert "[" not in cleaned
