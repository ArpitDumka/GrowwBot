from mf_compose.groq_client import StubLLMClient
from mf_compose.models import ComposeOutcome
from mf_compose.pipeline import chat


def test_refused_skips_llm():
    r = chat("Should I invest in HDFC Mid Cap?", test_reranker=True, llm=StubLLMClient("unused"))
    assert r.compose.outcome == ComposeOutcome.REFUSED
    assert r.compose.used_llm is False


def test_elss_exit_load_mock_llm():
    llm = StubLLMClient(
        "The exit load on HDFC ELSS Tax Saver Fund is Nil.\n"
        "Source: https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth\n"
        "Last updated from sources: 2026-05-16"
    )
    r = chat(
        "What is the exit load on HDFC ELSS Tax Saver Fund?",
        test_reranker=True,
        llm=llm,
    )
    assert r.compose.outcome == ComposeOutcome.ANSWERED
    assert "nil" in r.compose.text.lower()
