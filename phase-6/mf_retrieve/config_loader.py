"""Load ``config/retrieval.yaml``."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from mf_retrieve.paths import RETRIEVAL_YAML


@dataclass(frozen=True)
class RetrievalConfig:
    hybrid_top_k: int = 5
    field_boost: float = 0.12
    section_boost: float = 0.08
    primary_section_bonus: float = 0.15
    section_mismatch_penalty: float = 0.25
    rerank_weight: float = 0.55
    hybrid_weight: float = 0.45
    rerank_model: str = "BAAI/bge-reranker-base"
    rerank_top_n: int = 5
    max_context_chunks: int = 1
    tau_hard: float = 0.35
    tau_soft: float = 0.25
    exclude_doc_types: tuple[str, ...] = ("performance",)
    field_section_map: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def preferred_sections(self, field_id: str | None) -> tuple[str, ...]:
        if not field_id or not self.field_section_map:
            return ()
        return self.field_section_map.get(field_id, ())


def _parse_field_map(raw: dict[str, Any] | None) -> dict[str, tuple[str, ...]]:
    out: dict[str, tuple[str, ...]] = {}
    for key, val in (raw or {}).items():
        if isinstance(val, list):
            out[str(key)] = tuple(str(x) for x in val)
    return out


@lru_cache(maxsize=1)
def load_retrieval_config(path: Path = RETRIEVAL_YAML) -> RetrievalConfig:
    if not path.is_file():
        raise FileNotFoundError(f"retrieval config missing: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return RetrievalConfig(
        hybrid_top_k=int(data.get("hybrid_top_k", 5)),
        field_boost=float(data.get("field_boost", 0.12)),
        section_boost=float(data.get("section_boost", 0.08)),
        primary_section_bonus=float(data.get("primary_section_bonus", 0.15)),
        section_mismatch_penalty=float(data.get("section_mismatch_penalty", 0.25)),
        rerank_weight=float(data.get("rerank_weight", 0.55)),
        hybrid_weight=float(data.get("hybrid_weight", 0.45)),
        rerank_model=str(data.get("rerank_model", "BAAI/bge-reranker-base")),
        rerank_top_n=int(data.get("rerank_top_n", 5)),
        max_context_chunks=int(data.get("max_context_chunks", 1)),
        tau_hard=float(data.get("tau_hard", 0.35)),
        tau_soft=float(data.get("tau_soft", 0.25)),
        exclude_doc_types=tuple(str(x) for x in (data.get("exclude_doc_types") or ["performance"])),
        field_section_map=_parse_field_map(data.get("field_section_map")),
    )
