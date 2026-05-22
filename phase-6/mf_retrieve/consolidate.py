"""§6.1 [E] tiebreak and top-1 selection."""

from __future__ import annotations

from mf_retrieve.config_loader import RetrievalConfig
from mf_retrieve.models import RetrievedChunk
from mf_index.models import ChunkRecord


def _tiebreak_key(c: ChunkRecord, scheme: str | None) -> tuple:
    scheme_match = 0 if scheme and c.scheme == scheme else 1
    return (scheme_match, c.last_updated, -len(c.text))


def chunk_record_to_retrieved(
    c: ChunkRecord,
    *,
    hybrid_score: float = 0.0,
    boost: float = 0.0,
    rerank_score: float = 0.0,
    final_score: float = 0.0,
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=c.chunk_id,
        text=c.text,
        scheme=c.scheme,
        section=c.section,
        source_id=c.source_id,
        url=c.url,
        last_updated=c.last_updated,
        fields_detected=tuple(c.fields_detected),
        doc_type=c.doc_type,
        hybrid_score=hybrid_score,
        boost=boost,
        rerank_score=rerank_score,
        final_score=final_score,
    )


def pick_top_chunks(
    ranked: list[tuple[ChunkRecord, float, float, float, float]],
    scheme: str | None,
    cfg: RetrievalConfig,
) -> list[RetrievedChunk]:
    """ranked: (chunk, hybrid, boost, rerank, final) sorted by final desc."""
    if not ranked:
        return []
    # Stable tiebreak on equal final score
    ranked = sorted(
        ranked,
        key=lambda row: (-row[4], *_tiebreak_key(row[0], scheme)),
    )
    top = ranked[0]
    c, hs, b, rs, fs = top
    out = [
        chunk_record_to_retrieved(
            c, hybrid_score=hs, boost=b, rerank_score=rs, final_score=fs
        )
    ]
    if cfg.max_context_chunks > 1:
        for row in ranked[1 : cfg.max_context_chunks]:
            c2, hs2, b2, rs2, fs2 = row
            if abs(fs2 - fs) < 1e-6:
                out.append(
                    chunk_record_to_retrieved(
                        c2, hybrid_score=hs2, boost=b2, rerank_score=rs2, final_score=fs2
                    )
                )
    return out


def confidence_band(final_score: float, cfg: RetrievalConfig) -> str:
    if final_score < cfg.tau_hard:
        return "not_found"
    if final_score < cfg.tau_soft:
        return "low"
    return "ok"
