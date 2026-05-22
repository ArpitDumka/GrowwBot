"""Hybrid BM25 + vector retrieval (architecture §4.3)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from mf_index.bm25_index import BM25Index
from mf_index.embedder import Embedder
from mf_index.models import ChunkRecord
from mf_index.paths import DEFAULT_ALPHA
from mf_index.vector_store import ChromaVectorStore


@dataclass
class SearchHit:
    chunk_id: str
    score: float
    vector_score: float
    bm25_score: float
    scheme: str
    section: str
    doc_type: str
    text_preview: str


def _min_max_norm(scores: dict[str, float]) -> dict[str, float]:
    if not scores:
        return {}
    vals = list(scores.values())
    lo, hi = min(vals), max(vals)
    if hi <= lo:
        return {k: 1.0 if v > 0 else 0.0 for k, v in scores.items()}
    return {k: (v - lo) / (hi - lo) for k, v in scores.items()}


def _indices_for_filter(chunks: list[ChunkRecord], where: dict[str, Any] | None) -> list[int] | None:
    if not where:
        return None
    allowed: list[int] = []
    for i, c in enumerate(chunks):
        ok = True
        for key, val in where.items():
            attr = getattr(c, key, None)
            if attr != val:
                ok = False
                break
        if ok:
            allowed.append(i)
    return allowed


class HybridIndex:
    """In-memory view over Chroma + BM25 for combined scoring."""

    def __init__(
        self,
        *,
        chunks: list[ChunkRecord],
        embedder: Embedder,
        vector_store: ChromaVectorStore,
        bm25: BM25Index,
        alpha: float = DEFAULT_ALPHA,
    ) -> None:
        self.chunks = chunks
        self.embedder = embedder
        self.vector_store = vector_store
        self.bm25 = bm25
        self.alpha = alpha
        self._id_to_chunk = {c.chunk_id: c for c in chunks}

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[SearchHit]:
        chroma_where = where
        q_vec = self.embedder.embed_query(query)
        n = max(top_k * 3, 10)
        vres = self.vector_store.query(q_vec, n_results=n, where=chroma_where)

        vec_scores: dict[str, float] = {}
        ids = (vres.get("ids") or [[]])[0]
        dists = (vres.get("distances") or [[]])[0]
        for cid, dist in zip(ids, dists, strict=False):
            # cosine distance in Chroma: 0 = identical
            vec_scores[cid] = max(0.0, 1.0 - float(dist))

        allowed = _indices_for_filter(self.chunks, where)
        bm25_raw = self.bm25.scores(query, allowed_indices=allowed)
        bm25_by_id = {
            self.bm25.chunk_ids[i]: bm25_raw[i] for i in range(len(self.bm25.chunk_ids))
        }

        if allowed is not None:
            candidate_ids = {self.chunks[i].chunk_id for i in allowed}
        else:
            candidate_ids = set(self.bm25.chunk_ids)
        candidate_ids |= set(vec_scores)

        v_norm = _min_max_norm({cid: vec_scores.get(cid, 0.0) for cid in candidate_ids})
        b_norm = _min_max_norm({cid: bm25_by_id.get(cid, 0.0) for cid in candidate_ids})

        combined: list[tuple[str, float, float, float]] = []
        for cid in candidate_ids:
            vs = v_norm.get(cid, 0.0)
            bs = b_norm.get(cid, 0.0)
            final = self.alpha * vs + (1.0 - self.alpha) * bs
            combined.append((cid, final, vs, bs))

        combined.sort(key=lambda x: x[1], reverse=True)
        hits: list[SearchHit] = []
        for cid, final, vs, bs in combined[:top_k]:
            c = self._id_to_chunk.get(cid)
            if not c:
                continue
            preview = c.text[:200] + ("…" if len(c.text) > 200 else "")
            hits.append(
                SearchHit(
                    chunk_id=cid,
                    score=final,
                    vector_score=vs,
                    bm25_score=bs,
                    scheme=c.scheme,
                    section=c.section,
                    doc_type=c.doc_type,
                    text_preview=preview,
                )
            )
        return hits
