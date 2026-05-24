"""Tests for mf_insights builder."""

from __future__ import annotations

from mf_insights.builder import build_insights_payload
from mf_insights.paths import CHUNKS_JSONL, DASHBOARD_SOURCE_IDS


def test_build_insights_from_corpus() -> None:
    assert CHUNKS_JSONL.is_file(), "chunks.jsonl required for insights build"
    payload = build_insights_payload()
    funds = payload["funds"]
    assert len(funds) == len(DASHBOARD_SOURCE_IDS)
    sample = funds[0]
    assert sample["nav"] > 0
    assert sample["expenseRatio"] >= 0
    assert "returns" in sample
    assert payload["portfolioHoldings"]
    assert payload["marketFacts"]
    assert payload["lastUpdated"]
