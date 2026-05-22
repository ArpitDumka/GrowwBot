"""§3.6 corpus size reporting."""

from __future__ import annotations

import pytest

from mf_clean.chunk_models import Chunk
from mf_clean.corpus_stats import (
    assert_chunk_count_in_bounds,
    expected_chunk_bounds,
    summarize_chunk_corpus,
)


def _chunk(section: str, **kwargs: str) -> Chunk:
    base = dict(
        chunk_id=f"src1#{section}",
        text="word " * 40,
        source_id="src1",
        url="https://groww.in/mutual-funds/x",
        section=section,
        scheme="S",
        category="Mid Cap",
        publisher="Groww",
        last_updated="2026-05-14",
        fields_detected=["exit_load"],
        doc_type="facts",
    )
    base.update(kwargs)
    return Chunk.model_validate(base)


def test_expected_chunk_bounds_default() -> None:
    lo, hi = expected_chunk_bounds()
    assert lo == 60 and hi == 80


def test_summarize_chunk_corpus() -> None:
    chunks = [
        _chunk("header"),
        _chunk("exit_load_tax"),
        _chunk("performance", doc_type="performance", fields_detected=[]),
    ]
    rep = summarize_chunk_corpus(chunks, num_registry_sources=10)
    assert rep.num_chunks == 3
    assert rep.facts_chunks == 2
    assert rep.performance_chunks == 1
    assert rep.num_distinct_sources == 1
    assert rep.within_nominal_bounds is False
    assert rep.chunks_by_section["header"] == 1


def test_assert_chunk_count_in_bounds() -> None:
    chunks = [
        _chunk(f"sec{n}", chunk_id=f"src{n % 3}#sec{n}", source_id=f"src{n % 3}")
        for n in range(60)
    ]
    assert_chunk_count_in_bounds(chunks)
    with pytest.raises(AssertionError):
        assert_chunk_count_in_bounds(chunks[:5])
