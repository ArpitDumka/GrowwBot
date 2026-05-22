"""Combine hybrid, boosts, rerank, and section routing into a final score."""

from __future__ import annotations

from mf_retrieve.config_loader import RetrievalConfig
from mf_index.models import ChunkRecord


def _normalize_by_max(values: list[float]) -> list[float]:
    """Scale by top score so the best hybrid+boost candidate keeps full weight."""
    if not values:
        return []
    hi = max(values)
    if hi <= 0:
        return [0.0] * len(values)
    return [v / hi for v in values]


def section_adjustment(
    chunk: ChunkRecord,
    field_id: str | None,
    cfg: RetrievalConfig,
) -> float:
    if not field_id:
        return 0.0
    preferred = cfg.preferred_sections(field_id)
    if not preferred:
        return 0.0
    if chunk.section not in preferred:
        return -cfg.section_mismatch_penalty
    if chunk.section == preferred[0]:
        return cfg.primary_section_bonus
    return 0.0


def combine_final_scores(
    rows: list[tuple[ChunkRecord, float, float, float]],
    field_id: str | None,
    cfg: RetrievalConfig,
) -> list[tuple[ChunkRecord, float, float, float, float]]:
    """Input: (chunk, hybrid_score, boost, rerank_score). Output adds final_score."""
    hybrid_boosted = [r[1] + r[2] for r in rows]
    norm_hybrid = _normalize_by_max(hybrid_boosted)
    out: list[tuple[ChunkRecord, float, float, float, float]] = []
    for (chunk, hybrid, boost, rerank), nh in zip(rows, norm_hybrid, strict=False):
        adj = section_adjustment(chunk, field_id, cfg)
        final = cfg.rerank_weight * rerank + cfg.hybrid_weight * nh + adj
        final = max(0.0, min(1.0, final))
        out.append((chunk, hybrid, boost, rerank, final))
    out.sort(key=lambda r: (-r[4], r[0].last_updated, -len(r[0].text)))
    return out
