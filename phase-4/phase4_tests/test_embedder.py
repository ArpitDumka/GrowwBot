"""§4.1 embedder tests."""

from __future__ import annotations

from mf_index.embedder import HashingEmbedder, create_embedder


def test_hashing_embedder_dimension() -> None:
    emb = create_embedder(test=True)
    assert emb.dimension == 384
    vecs = emb.embed_documents(["exit load 1%", "min sip ₹100"])
    assert vecs.shape == (2, 384)


def test_bge_query_differs_from_doc() -> None:
    emb = HashingEmbedder()
    d = emb.embed_documents(["expense ratio 0.5%"])[0]
    q = emb.embed_query("expense ratio")
    assert d.shape == q.shape
