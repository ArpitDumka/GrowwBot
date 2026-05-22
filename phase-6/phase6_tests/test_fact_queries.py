"""Integration: problem-statement fact queries retrieve the right sections."""

from mf_retrieve.pipeline import ask

CASES = [
    (
        "expense_ratio",
        "What is the expense ratio of HDFC Mid Cap Fund?",
        "hdfc_midcap#header",
        ("0.75", "expense"),
    ),
    (
        "exit_load",
        "What is the exit load on HDFC Mid Cap Fund?",
        "hdfc_midcap#exit_load_tax",
        ("exit load", "1%"),
    ),
    (
        "min_sip",
        "What is the minimum SIP for HDFC Mid Cap Fund?",
        ("hdfc_midcap#about", "hdfc_midcap#minimum_investments"),
        ("100", "sip"),
    ),
    (
        "lock_in",
        "What is the lock-in period of HDFC ELSS Tax Saver Fund?",
        ("hdfc_elss#lock_in_banner", "hdfc_elss#about", "hdfc_elss#header"),
        ("lock", "3"),
    ),
    (
        "risk",
        "What is the riskometer of HDFC Mid Cap Fund?",
        "hdfc_midcap#about",
        ("risk", "very high"),
    ),
    (
        "benchmark",
        "What is the benchmark of HDFC Mid Cap Fund?",
        "hdfc_midcap#about",
        ("benchmark", "midcap", "nifty"),
    ),
]


def test_fact_query_chunks():
    for _label, query, expected_chunks, text_hints in CASES:
        r = ask(query, test_reranker=True)
        assert r.retrieval is not None and r.retrieval.chunks, f"{query}: no chunk"
        chunk = r.retrieval.chunks[0]
        allowed = (expected_chunks,) if isinstance(expected_chunks, str) else expected_chunks
        assert chunk.chunk_id in allowed, f"{query}: got {chunk.chunk_id}"
        lower = chunk.text.casefold()
        assert any(h in lower for h in text_hints), f"{query}: missing fact in {chunk.chunk_id}"


def test_statement_download_refused():
    from mf_guard.pipeline import process_query
    from mf_guard.models import Outcome

    r = process_query("How do I download capital gains report for HDFC Mid Cap Fund?")
    assert r.outcome == Outcome.REFUSE
