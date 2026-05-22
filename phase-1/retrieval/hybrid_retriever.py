"""Phase 6 — Hybrid retriever.

Pipeline (``docs/architecture.md`` §6.1):
    [A] metadata pre-filter (scheme/section)
    [B] hybrid search (vector + BM25)
    [C] cross-encoder re-rank
    [D] source consolidation -> 1-3 context chunks

Two-band threshold: ``hard_tau`` -> NOT_FOUND, ``soft_tau`` -> answer with
low-confidence hint. See ``docs/edge-cases/phase-6-retrieval.md`` 6.01.
"""
