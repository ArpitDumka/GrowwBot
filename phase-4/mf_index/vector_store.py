"""Chroma vector store (architecture §4.2)."""

from __future__ import annotations

from typing import Any

import numpy as np

from mf_index.models import ChunkRecord
from mf_index.paths import CHROMA_DIR

COLLECTION_NAME = "mf_faq_chunks"


def _chunk_metadata(c: ChunkRecord) -> dict[str, str | int | float | bool]:
    return {
        "chunk_id": c.chunk_id,
        "source_id": c.source_id,
        "scheme": c.scheme,
        "category": c.category,
        "section": c.section,
        "url": c.url,
        "last_updated": c.last_updated,
        "fields_detected": ",".join(c.fields_detected),
        "doc_type": c.doc_type,
        "publisher": c.publisher,
    }


class ChromaVectorStore:
    def __init__(self, persist_dir: str | None = None) -> None:
        import chromadb

        path = str(persist_dir or CHROMA_DIR)
        self._client = chromadb.PersistentClient(path=path)
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    @property
    def count(self) -> int:
        return self._collection.count()

    def reset_and_upsert(
        self,
        chunks: list[ChunkRecord],
        embeddings: np.ndarray,
        *,
        embedding_model: str,
    ) -> None:
        if len(chunks) != embeddings.shape[0]:
            raise ValueError("chunks and embeddings length mismatch")
        try:
            self._client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine", "embedding_model": embedding_model},
        )
        ids = [c.chunk_id for c in chunks]
        documents = [c.text for c in chunks]
        metadatas = [_chunk_metadata(c) for c in chunks]
        self._collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings.tolist(),
            metadatas=metadatas,
        )

    def query(
        self,
        query_embedding: np.ndarray,
        *,
        n_results: int = 10,
        where: dict[str, Any] | None = None,
    ) -> dict[str, list]:
        kwargs: dict[str, Any] = {
            "query_embeddings": [query_embedding.tolist()],
            "n_results": min(n_results, max(self.count, 1)),
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where
        return self._collection.query(**kwargs)

    def get_all(
        self,
        *,
        include_embeddings: bool = True,
    ) -> dict[str, list]:
        """Return every row in the collection (for Parquet / audit export)."""
        include: list[str] = ["metadatas", "documents"]
        if include_embeddings:
            include.append("embeddings")
        return self._collection.get(include=include)
