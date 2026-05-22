"""End-to-end ask: Phase 5 guard + Phase 6 retrieval."""

from __future__ import annotations

from mf_retrieve.config_loader import RetrievalConfig, load_retrieval_config
from mf_retrieve.models import AskResult
from mf_retrieve.reranker import BaseReranker, create_reranker
from mf_retrieve.retriever import retrieve


def ensure_phase_paths() -> None:
    import sys
    from mf_retrieve.paths import PHASE4_ROOT, PHASE5_ROOT

    for root in (PHASE4_ROOT, PHASE5_ROOT):
        p = str(root.resolve())
        if p not in sys.path:
            sys.path.insert(0, p)


def load_index(*, test_embedder: bool = False):
    ensure_phase_paths()
    from mf_index.build_index import load_hybrid_index  # noqa: PLC0415
    from mf_index.embedder import create_embedder  # noqa: PLC0415

    emb = create_embedder(test=test_embedder)
    return load_hybrid_index(embedder=emb)


def ask(
    query: str,
    index=None,
    *,
    cfg: RetrievalConfig | None = None,
    test_embedder: bool = False,
    test_reranker: bool = False,
    reranker: BaseReranker | None = None,
) -> AskResult:
    ensure_phase_paths()
    from mf_guard.models import Outcome  # noqa: PLC0415
    from mf_guard.pipeline import process_query  # noqa: PLC0415

    guard = process_query(query)
    if guard.outcome != Outcome.PROCEED:
        return AskResult(guard=guard, retrieval=None)

    cfg = cfg or load_retrieval_config()
    idx = index or load_index(test_embedder=test_embedder)
    rr = reranker
    if rr is None and test_reranker:
        rr = create_reranker(cfg.rerank_model, test=True)
    retrieval = retrieve(
        guard,
        idx,
        cfg=cfg,
        reranker=rr,
        passthrough_rerank=test_reranker,
    )
    return AskResult(guard=guard, retrieval=retrieval)
