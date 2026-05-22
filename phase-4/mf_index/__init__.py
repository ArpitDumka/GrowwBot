"""Phase 4 — embedding & hybrid index (MF FAQ assistant)."""

from mf_index.build_index import BuildReport, build_hybrid_index, load_hybrid_index
from mf_index.embedder import BGEEmbedder, Embedder, create_embedder
from mf_index.hybrid import HybridIndex, SearchHit

__all__ = [
    "BGEEmbedder",
    "BuildReport",
    "Embedder",
    "HybridIndex",
    "SearchHit",
    "build_hybrid_index",
    "create_embedder",
    "load_hybrid_index",
]
