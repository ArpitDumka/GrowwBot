from mf_compose.pipeline import chat
from mf_retrieve.pipeline import ask


def test_scheme_label_only_uses_about_not_not_found():
    r = ask("hdfc mid cap fund", test_reranker=True)
    assert r.retrieval is not None
    assert r.retrieval.outcome.value == "FOUND"
    assert r.retrieval.chunks[0].chunk_id == "hdfc_midcap#about"


def test_scheme_only_hint_without_llm():
    r = chat("hdfc mid cap fund", test_reranker=True, llm=None)
    assert r.compose.outcome.value == "ANSWERED"
    assert "expense ratio" in r.compose.text.lower()
    assert "Source: https://" in r.compose.text
