"""Integration: NAV queries must retrieve about-section chunks (real index)."""

from mf_retrieve.pipeline import ask


def test_midcap_nav_retrieves_about_chunk():
    r = ask("What is the NAV of HDFC Mid Cap Fund?", test_reranker=True)
    assert r.retrieval is not None
    assert r.retrieval.outcome.value == "FOUND"
    chunk = r.retrieval.chunks[0]
    assert chunk.chunk_id.endswith("#about")
    assert "nav" in chunk.fields_detected or "NAV" in chunk.text or "218" in chunk.text
