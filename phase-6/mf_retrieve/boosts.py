"""§6.1 [C] additive field and section boosts."""

from __future__ import annotations

from mf_retrieve.config_loader import RetrievalConfig
from mf_index.hybrid import SearchHit
from mf_index.models import ChunkRecord


def compute_boost(
    chunk: ChunkRecord,
    field_id: str | None,
    cfg: RetrievalConfig,
) -> float:
    if not field_id:
        return 0.0
    bonus = 0.0
    if field_id in chunk.fields_detected:
        bonus += cfg.field_boost
    preferred = cfg.preferred_sections(field_id)
    if preferred and chunk.section in preferred:
        bonus += cfg.section_boost
    return bonus


def apply_boosts_to_hits(
    hits: list[SearchHit],
    id_to_chunk: dict[str, ChunkRecord],
    field_id: str | None,
    cfg: RetrievalConfig,
) -> list[tuple[SearchHit, ChunkRecord, float]]:
    scored: list[tuple[SearchHit, ChunkRecord, float]] = []
    for h in hits:
        c = id_to_chunk.get(h.chunk_id)
        if not c:
            continue
        boost = compute_boost(c, field_id, cfg)
        scored.append((h, c, h.score + boost))
    scored.sort(key=lambda x: x[2], reverse=True)
    return scored
