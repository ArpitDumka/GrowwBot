"""Retrieval layer (Phases 4 + 6).

- ``embedder``: pluggable embedding model interface.
- ``vector_store``: Chroma wrapper.
- ``bm25``: rank_bm25 wrapper.
- ``hybrid_retriever``: vector + BM25 + cross-encoder re-rank.
"""
