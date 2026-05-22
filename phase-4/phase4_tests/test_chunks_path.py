"""Portable chunks_path in index manifest (Docker / Render)."""

from mf_index.build_index import resolve_chunks_path
from mf_index.paths import CHUNKS_JSONL, REPO_ROOT


def test_resolve_relative_manifest_path():
    manifest = {"chunks_path": "phase-3/data/chunks.jsonl"}
    assert resolve_chunks_path(manifest) == CHUNKS_JSONL


def test_resolve_falls_back_when_absolute_missing():
    manifest = {"chunks_path": r"C:\nonexistent\chunks.jsonl"}
    assert resolve_chunks_path(manifest) == CHUNKS_JSONL


def test_manifest_stored_relative():
    raw = (REPO_ROOT / "phase-4" / "data" / "index" / "index_manifest.json").read_text(encoding="utf-8")
    assert r"C:\Users" not in raw or "phase-3/data/chunks.jsonl" in raw
