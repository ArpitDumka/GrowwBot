import pytest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MANIFEST = REPO / "phase-4" / "data" / "index" / "index_manifest.json"


@pytest.mark.skipif(not MANIFEST.is_file(), reason="Phase 4 index not built")
def test_ask_factual_midcap():
    from mf_retrieve.pipeline import ask
    from mf_guard.models import Outcome
    from mf_retrieve.models import RetrievalOutcome

    res = ask(
        "What is the expense ratio of HDFC Mid Cap Fund?",
        test_reranker=True,
    )
    assert res.guard.outcome == Outcome.PROCEED
    assert res.retrieval is not None
    assert res.retrieval.outcome == RetrievalOutcome.FOUND
    assert "hdfc_midcap" in res.retrieval.chunks[0].chunk_id
