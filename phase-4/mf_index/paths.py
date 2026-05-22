"""Repository-relative paths (Phase 4 package lives in ``phase-4/``)."""

from __future__ import annotations

from pathlib import Path

PHASE4_ROOT: Path = Path(__file__).resolve().parent.parent
REPO_ROOT: Path = PHASE4_ROOT.parent
PHASE1_ROOT: Path = REPO_ROOT / "phase-1"
PHASE3_ROOT: Path = REPO_ROOT / "phase-3"

SOURCES_YAML: Path = PHASE1_ROOT / "config" / "sources.yaml"
CHUNKS_JSONL: Path = PHASE3_ROOT / "data" / "chunks.jsonl"
BM25_STOPWORDS: Path = PHASE4_ROOT / "config" / "bm25_stopwords.txt"

INDEX_ROOT: Path = PHASE4_ROOT / "data" / "index"
CHROMA_DIR: Path = INDEX_ROOT / "chroma"
BM25_DIR: Path = INDEX_ROOT / "bm25"
BACKUPS_DIR: Path = INDEX_ROOT / "backups"
MANIFEST_PATH: Path = INDEX_ROOT / "index_manifest.json"
BUILD_LOCK_PATH: Path = INDEX_ROOT / ".build.lock"

DEFAULT_MODEL_ID = "BAAI/bge-small-en-v1.5"
DEFAULT_ALPHA = 0.6
