"""Phase 6 retriever — orchestrates filter → hybrid → boost → rerank."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from mf_retrieve.boosts import apply_boosts_to_hits
from mf_retrieve.config_loader import RetrievalConfig, load_retrieval_config
from mf_retrieve.consolidate import chunk_record_to_retrieved, confidence_band, pick_top_chunks
from mf_retrieve.filters import (
    find_field_chunk,
    find_header_chunk,
    find_section_chunk,
    filter_scheme_chunks,
)
from mf_retrieve.query_shape import is_scheme_only_query
from mf_retrieve.scoring import combine_final_scores
from mf_retrieve.models import RetrievalOutcome, RetrievalResult
from mf_retrieve.reranker import BaseReranker, PassthroughReranker, create_reranker
from mf_retrieve.templates import not_found_message

if TYPE_CHECKING:
    from mf_guard.models import GuardResult
    from mf_index.hybrid import HybridIndex

log = logging.getLogger(__name__)


def _id_map(index: HybridIndex) -> dict:
    return {c.chunk_id: c for c in index.chunks}


def retrieve(
    guard: GuardResult,
    index: HybridIndex,
    *,
    cfg: RetrievalConfig | None = None,
    reranker: BaseReranker | None = None,
    passthrough_rerank: bool = False,
) -> RetrievalResult:
    """Run Phase 6 on a Phase 5 PROCEED result."""
    from mf_guard.models import Outcome  # noqa: PLC0415

    cfg = cfg or load_retrieval_config()
    id_to_chunk = _id_map(index)

    if guard.outcome != Outcome.PROCEED:
        return RetrievalResult(
            outcome=RetrievalOutcome.SKIPPED,
            message="Guard did not proceed to retrieval.",
            log_safe={"guard_intent": guard.intent.value},
        )

    if not index.chunks:
        return RetrievalResult(
            outcome=RetrievalOutcome.NOT_FOUND,
            message="System is still indexing — try again shortly.",
            log_safe={"reason": "empty_index"},
        )

    query = guard.rewritten_query or guard.working_query
    field_id = guard.field_id
    scheme_match = guard.schemes[0] if guard.schemes else None
    scheme = scheme_match.canonical if scheme_match else None
    groww_url = scheme_match.groww_url if scheme_match else None
    source_id = scheme_match.source_id if scheme_match else None

    if not scheme:
        from mf_guard.conversational import classify_conversational, looks_like_fund_question

        if not looks_like_fund_question(query) and classify_conversational(query):
            return RetrievalResult(
                outcome=RetrievalOutcome.SKIPPED,
                message="",
                field_id=field_id,
                log_safe={"reason": "conversational_deferred_to_compose"},
            )
        return RetrievalResult(
            outcome=RetrievalOutcome.NOT_FOUND,
            message=not_found_message(None),
            field_id=field_id,
            log_safe={"reason": "no_scheme"},
        )

    preferred = cfg.preferred_sections(field_id)
    if field_id and source_id:
        field_chunk = find_field_chunk(
            index.chunks, source_id, field_id, preferred, cfg.exclude_doc_types
        )
        if field_chunk:
            return RetrievalResult(
                outcome=RetrievalOutcome.FOUND,
                chunks=[
                    chunk_record_to_retrieved(
                        field_chunk, hybrid_score=1.0, boost=cfg.field_boost, final_score=1.0
                    )
                ],
                scheme=scheme,
                groww_url=groww_url,
                field_id=field_id,
                log_safe={"chunk_id": field_chunk.chunk_id, "fast_path": "field"},
            )

    # Scheme label only (e.g. "hdfc mid cap fund") → prompt user for a specific fact.
    if not field_id and source_id and is_scheme_only_query(query):
        about = find_section_chunk(index.chunks, source_id, "about", cfg.exclude_doc_types)
        if about:
            return RetrievalResult(
                outcome=RetrievalOutcome.FOUND,
                chunks=[
                    chunk_record_to_retrieved(about, hybrid_score=1.0, final_score=1.0)
                ],
                scheme=scheme,
                groww_url=groww_url,
                field_id=None,
                log_safe={"chunk_id": about.chunk_id, "fast_path": "scheme_overview"},
            )

    # §6.11 header fast-path (factual questions without a resolved field tag)
    if not field_id and source_id and not is_scheme_only_query(query):
        header = find_header_chunk(index.chunks, source_id)
        if header:
            return RetrievalResult(
                outcome=RetrievalOutcome.FOUND,
                chunks=[
                    chunk_record_to_retrieved(header, hybrid_score=1.0, final_score=1.0)
                ],
                scheme=scheme,
                groww_url=groww_url,
                field_id=None,
                used_header_fast_path=True,
                log_safe={"chunk_id": header.chunk_id, "fast_path": "header"},
            )

    where = {"scheme": scheme}
    hits = index.search(query, top_k=cfg.hybrid_top_k, where=where)
    hits = [h for h in hits if id_to_chunk.get(h.chunk_id) and id_to_chunk[h.chunk_id].doc_type not in cfg.exclude_doc_types]

    fallback = False
    if not hits:
        scheme_chunks = filter_scheme_chunks(index.chunks, scheme, cfg.exclude_doc_types)
        if scheme_chunks:
            hits = index.search(query, top_k=cfg.hybrid_top_k, where={"scheme": scheme})
            hits = [
                h
                for h in hits
                if id_to_chunk.get(h.chunk_id)
                and id_to_chunk[h.chunk_id].doc_type not in cfg.exclude_doc_types
            ]
            fallback = True

    if not hits:
        about = (
            find_section_chunk(index.chunks, source_id, "about", cfg.exclude_doc_types)
            if source_id
            else None
        )
        if about:
            return RetrievalResult(
                outcome=RetrievalOutcome.FOUND,
                chunks=[chunk_record_to_retrieved(about, hybrid_score=0.5, final_score=0.5)],
                scheme=scheme,
                groww_url=groww_url,
                field_id=field_id,
                fallback_no_filter=fallback,
                log_safe={"chunk_id": about.chunk_id, "fast_path": "about_fallback"},
            )
        return RetrievalResult(
            outcome=RetrievalOutcome.NOT_FOUND,
            message=not_found_message(groww_url),
            scheme=scheme,
            groww_url=groww_url,
            field_id=field_id,
            fallback_no_filter=fallback,
            log_safe={"reason": "no_hybrid_hits", "index_chunks": len(index.chunks)},
        )

    boosted = apply_boosts_to_hits(hits, id_to_chunk, field_id, cfg)
    top_n = boosted[: cfg.rerank_top_n]

    pre_scores = [s for _, _, s in top_n]
    rr = reranker
    reranker_used = False
    if passthrough_rerank:
        rerank_scores = PassthroughReranker(pre_scores).score(query, [c.text for _, c, _ in top_n])
    elif rr is None:
        rr = create_reranker(cfg.rerank_model)
        if rr.is_available:
            rerank_scores = rr.score(query, [c.text for _, c, _ in top_n])
            reranker_used = True
        else:
            rerank_scores = PassthroughReranker(pre_scores).score(
                query, [c.text for _, c, _ in top_n]
            )
    elif rr.is_available:
        rerank_scores = rr.score(query, [c.text for _, c, _ in top_n])
        reranker_used = True
    else:
        rerank_scores = PassthroughReranker(pre_scores).score(query, [c.text for _, c, _ in top_n])

    score_rows: list[tuple] = []
    for (hit, chunk, hybrid_plus_boost), rs in zip(top_n, rerank_scores, strict=False):
        boost_only = hybrid_plus_boost - hit.score
        score_rows.append((chunk, hit.score, boost_only, float(rs)))

    ranked = combine_final_scores(score_rows, field_id, cfg)
    picked = pick_top_chunks(ranked, scheme, cfg)
    if not picked:
        return RetrievalResult(
            outcome=RetrievalOutcome.NOT_FOUND,
            message=not_found_message(groww_url),
            scheme=scheme,
            groww_url=groww_url,
            field_id=field_id,
        )

    top_score = picked[0].final_score
    band = confidence_band(top_score, cfg)
    if band == "not_found":
        return RetrievalResult(
            outcome=RetrievalOutcome.NOT_FOUND,
            message=not_found_message(groww_url),
            scheme=scheme,
            groww_url=groww_url,
            field_id=field_id,
            reranker_used=reranker_used,
            log_safe={"top_score": top_score, "tau_hard": cfg.tau_hard},
        )

    return RetrievalResult(
        outcome=RetrievalOutcome.FOUND,
        chunks=picked,
        low_confidence=(band == "low"),
        scheme=scheme,
        groww_url=groww_url,
        field_id=field_id,
        reranker_used=reranker_used,
        fallback_no_filter=fallback,
        log_safe={
            "chunk_id": picked[0].chunk_id,
            "section": picked[0].section,
            "top_score": top_score,
        },
    )
