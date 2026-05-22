"""§4.2–4.4 index build and metadata filter tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mf_index.build_index import build_hybrid_index, load_hybrid_index
from mf_index.embedder import create_embedder
import mf_index.build_index as bi_mod


@pytest.fixture
def built_index(tmp_path: Path, sample_chunks_path: Path, monkeypatch: pytest.MonkeyPatch):
    import mf_index.build_index as bi
    import mf_index.bm25_index as bm25_mod
    import mf_index.paths as paths
    import mf_index.vector_store as vs_mod

    index_root = tmp_path / "index"
    monkeypatch.setattr(paths, "INDEX_ROOT", index_root)
    monkeypatch.setattr(paths, "CHROMA_DIR", index_root / "chroma")
    monkeypatch.setattr(paths, "BM25_DIR", index_root / "bm25")
    monkeypatch.setattr(paths, "BACKUPS_DIR", index_root / "backups")
    monkeypatch.setattr(paths, "MANIFEST_PATH", index_root / "index_manifest.json")
    monkeypatch.setattr(paths, "BUILD_LOCK_PATH", index_root / ".build.lock")
    monkeypatch.setattr(bi, "INDEX_ROOT", index_root)
    monkeypatch.setattr(bi, "CHROMA_DIR", index_root / "chroma")
    monkeypatch.setattr(bi, "BM25_DIR", index_root / "bm25")
    monkeypatch.setattr(bi, "BACKUPS_DIR", index_root / "backups")
    monkeypatch.setattr(bi, "MANIFEST_PATH", index_root / "index_manifest.json")
    monkeypatch.setattr(bi, "BUILD_LOCK_PATH", index_root / ".build.lock")
    monkeypatch.setattr(vs_mod, "CHROMA_DIR", index_root / "chroma")
    monkeypatch.setattr(bm25_mod, "BM25_DIR", index_root / "bm25")

    emb = create_embedder(test=True)
    hybrid, report = build_hybrid_index(
        chunks_path=sample_chunks_path,
        embedder=emb,
        use_lock=False,
    )
    return hybrid, report, emb


def test_build_writes_manifest(built_index) -> None:
    _, report, _ = built_index
    assert report.num_chunks == 3
    assert bi_mod.MANIFEST_PATH.is_file()
    data = json.loads(bi_mod.MANIFEST_PATH.read_text(encoding="utf-8"))
    assert data["embedding_model"] == "test/hashing"
    assert data["dimension"] == 384


def test_metadata_filter_scheme(built_index) -> None:
    idx, _, _ = built_index
    scheme = "HDFC Mid Cap Fund"
    hits = idx.search("exit load", top_k=10, where={"scheme": scheme})
    assert hits
    assert all(h.scheme == scheme for h in hits)


def test_load_hybrid_index_roundtrip(built_index) -> None:
    _, _, emb = built_index
    idx2 = load_hybrid_index(embedder=emb)
    assert len(idx2.chunks) == 3
