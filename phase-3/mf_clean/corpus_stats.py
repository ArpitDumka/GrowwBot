"""Expected corpus size helpers (architecture §3.6).

``10`` scheme pages × ``6–8`` sections each → about ``60–80`` chunks (before
merges / omissions). Used for sanity checks and CI reports — not a hard gate
unless you opt in via :func:`assert_chunk_count_in_bounds`.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field

from mf_clean.chunk_models import Chunk


def expected_chunk_bounds(
    num_schemes: int = 10,
    min_sections_per_scheme: int = 6,
    max_sections_per_scheme: int = 8,
) -> tuple[int, int]:
    """Return ``(min_chunks, max_chunks)`` for §3.6 nominal range."""
    return (
        num_schemes * min_sections_per_scheme,
        num_schemes * max_sections_per_scheme,
    )


@dataclass
class CorpusSizeReport:
    """Summary of a built chunk list vs §3.6 expectations."""

    num_chunks: int
    num_distinct_sources: int
    min_expected: int
    max_expected: int
    within_nominal_bounds: bool
    chunks_by_section: dict[str, int] = field(default_factory=dict)
    facts_chunks: int = 0
    performance_chunks: int = 0
    fields_nonempty_fraction: float = 0.0


def summarize_chunk_corpus(
    chunks: Sequence[Chunk],
    *,
    num_registry_sources: int = 10,
    min_sections: int = 6,
    max_sections: int = 8,
) -> CorpusSizeReport:
    """Aggregate counts; ``within_nominal_bounds`` uses §3.6 60–80 style range."""
    lst = list(chunks)
    lo, hi = expected_chunk_bounds(
        num_registry_sources,
        min_sections_per_scheme=min_sections,
        max_sections_per_scheme=max_sections,
    )
    by_sec = Counter(c.section for c in lst)
    facts = sum(1 for c in lst if c.doc_type == "facts")
    perf = sum(1 for c in lst if c.doc_type == "performance")
    nonempty = sum(1 for c in lst if c.fields_detected)
    frac = (nonempty / len(lst)) if lst else 0.0
    nsrc = len({c.source_id for c in lst})
    n = len(lst)
    return CorpusSizeReport(
        num_chunks=n,
        num_distinct_sources=nsrc,
        min_expected=lo,
        max_expected=hi,
        within_nominal_bounds=lo <= n <= hi,
        chunks_by_section=dict(sorted(by_sec.items())),
        facts_chunks=facts,
        performance_chunks=perf,
        fields_nonempty_fraction=round(frac, 4),
    )


def assert_chunk_count_in_bounds(
    chunks: Sequence[Chunk],
    *,
    num_registry_sources: int = 10,
    min_sections: int = 6,
    max_sections: int = 8,
) -> None:
    """Raise ``AssertionError`` if chunk count is wildly outside §3.6 nominal range."""
    rep = summarize_chunk_corpus(
        chunks,
        num_registry_sources=num_registry_sources,
        min_sections=min_sections,
        max_sections=max_sections,
    )
    assert rep.within_nominal_bounds, (
        f"chunk count {rep.num_chunks} outside §3.6 nominal range "
        f"[{rep.min_expected}, {rep.max_expected}]"
    )
