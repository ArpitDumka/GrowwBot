"""Build Chroma + BM25 indices from Phase 3 chunks (architecture §4)."""

from __future__ import annotations

import json
import logging
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mf_index.bm25_index import BM25Index
from mf_index.embedder import Embedder, create_embedder
from mf_index.hybrid import HybridIndex
from mf_index.lockfile import build_lock
from mf_index.models import ChunkRecord, content_hash, load_chunks_jsonl
from mf_index.normalize import normalize_for_embedding
from mf_index.paths import (
    BACKUPS_DIR,
    BM25_DIR,
    BUILD_LOCK_PATH,
    CHROMA_DIR,
    CHUNKS_JSONL,
    INDEX_ROOT,
    MANIFEST_PATH,
    REPO_ROOT,
)
from mf_index.sources import load_registry_source_ids
from mf_index.vector_store import ChromaVectorStore

log = logging.getLogger(__name__)


@dataclass
class BuildReport:
    num_chunks: int
    num_orphans_removed: int
    embedding_model: str
    dimension: int
    elapsed_s: float
    manifest_path: str


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


def _load_manifest(path: Path | None = None) -> dict[str, Any] | None:
    path = path or MANIFEST_PATH
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _filter_orphans(chunks: list[ChunkRecord], valid_ids: frozenset[str]) -> tuple[list[ChunkRecord], int]:
    kept = [c for c in chunks if c.source_id in valid_ids]
    return kept, len(chunks) - len(kept)


def _rotate_backup() -> None:
    if not INDEX_ROOT.is_dir():
        return
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    dest = BACKUPS_DIR / stamp
    if MANIFEST_PATH.is_file():
        dest.mkdir(parents=True, exist_ok=True)
        for name in ("index_manifest.json",):
            src = INDEX_ROOT / name
            if src.is_file():
                shutil.copy2(src, dest / name)
        if CHROMA_DIR.is_dir():
            shutil.copytree(CHROMA_DIR, dest / "chroma", dirs_exist_ok=True)
        if (BM25_DIR / "bm25.pkl").is_file():
            shutil.copytree(BM25_DIR, dest / "bm25", dirs_exist_ok=True)
        backups = sorted(BACKUPS_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        for old in backups[3:]:
            shutil.rmtree(old, ignore_errors=True)


def build_hybrid_index(
    *,
    chunks_path: Path = CHUNKS_JSONL,
    embedder: Embedder | None = None,
    full: bool = True,
    use_lock: bool = True,
) -> tuple[HybridIndex, BuildReport]:
    """Embed chunks, write Chroma + BM25 + manifest; return searchable index."""
    del full  # incremental diff reserved for future (edge 4.01)

    def _run() -> tuple[HybridIndex, BuildReport]:
        t0 = time.perf_counter()
        valid_ids = load_registry_source_ids()
        chunks = load_chunks_jsonl(chunks_path)
        chunks, n_orphan = _filter_orphans(chunks, valid_ids)

        emb = embedder or create_embedder()
        prev = _load_manifest()
        if prev:
            if prev.get("embedding_model") != emb.model_id or int(prev.get("dimension", -1)) != emb.dimension:
                log.warning(
                    "embedding model/dim changed (%s/%s -> %s/%s); full rebuild",
                    prev.get("embedding_model"),
                    prev.get("dimension"),
                    emb.model_id,
                    emb.dimension,
                )

        texts = [normalize_for_embedding(c.text) for c in chunks]
        log.info("Embedding %d chunks with %s …", len(chunks), emb.model_id)
        embeddings = emb.embed_documents(texts)

        _rotate_backup()

        bm25_tmp = BM25_DIR.with_name("bm25_build_tmp")
        if bm25_tmp.exists():
            shutil.rmtree(bm25_tmp, ignore_errors=True)

        # Chroma locks its persist dir on Windows — build in place, not rename.
        if CHROMA_DIR.exists():
            shutil.rmtree(CHROMA_DIR, ignore_errors=True)
        vs = ChromaVectorStore(persist_dir=str(CHROMA_DIR))
        vs.reset_and_upsert(chunks, embeddings, embedding_model=emb.model_id)
        del vs

        bm25 = BM25Index.build(chunks)
        bm25.save(bm25_tmp)
        if BM25_DIR.exists():
            shutil.rmtree(BM25_DIR, ignore_errors=True)
        bm25_tmp.replace(BM25_DIR)

        manifest = {
            "embedding_model": emb.model_id,
            "dimension": emb.dimension,
            "num_chunks": len(chunks),
            "chunk_ids": [c.chunk_id for c in chunks],
            "content_hashes": {c.chunk_id: content_hash(c.text) for c in chunks},
            "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "chunks_path": _manifest_chunks_path(chunks_path),
        }
        _atomic_write_json(MANIFEST_PATH, manifest)

        vs_final = ChromaVectorStore(persist_dir=str(CHROMA_DIR))
        bm25_final = BM25Index.load(BM25_DIR)
        hybrid = HybridIndex(
            chunks=chunks,
            embedder=emb,
            vector_store=vs_final,
            bm25=bm25_final,
        )
        elapsed = time.perf_counter() - t0
        report = BuildReport(
            num_chunks=len(chunks),
            num_orphans_removed=n_orphan,
            embedding_model=emb.model_id,
            dimension=emb.dimension,
            elapsed_s=elapsed,
            manifest_path=str(MANIFEST_PATH.resolve()),
        )
        return hybrid, report

    if use_lock:
        with build_lock(BUILD_LOCK_PATH):
            return _run()
    return _run()


def _manifest_chunks_path(chunks_path: Path) -> str:
    """Store repo-relative path so Docker/Render can load the index."""
    try:
        rel = chunks_path.resolve().relative_to(REPO_ROOT)
        return rel.as_posix()
    except ValueError:
        return "phase-3/data/chunks.jsonl"


def resolve_chunks_path(manifest: dict) -> Path:
    """Resolve ``chunks_path`` from manifest (portable across OS and Docker)."""
    raw = manifest.get("chunks_path")
    if raw:
        p = Path(str(raw))
        if p.is_file():
            return p
        candidate = REPO_ROOT / p
        if candidate.is_file():
            return candidate
    return CHUNKS_JSONL


def load_hybrid_index(embedder: Embedder | None = None) -> HybridIndex:
    manifest = _load_manifest()
    if not manifest:
        raise FileNotFoundError(f"index not built; run build first ({MANIFEST_PATH})")
    emb = embedder or create_embedder()
    if manifest.get("embedding_model") != emb.model_id:
        raise ValueError(
            f"manifest model {manifest.get('embedding_model')!r} != embedder {emb.model_id!r} (edge 4.02)"
        )
    if int(manifest.get("dimension", -1)) != emb.dimension:
        raise ValueError(
            f"manifest dim {manifest.get('dimension')} != embedder dim {emb.dimension} (edge 4.02)"
        )
    chunks_path = resolve_chunks_path(manifest)
    chunks = load_chunks_jsonl(chunks_path)
    valid = load_registry_source_ids()
    chunks, _ = _filter_orphans(chunks, valid)
    return HybridIndex(
        chunks=chunks,
        embedder=emb,
        vector_store=ChromaVectorStore(persist_dir=str(CHROMA_DIR)),
        bm25=BM25Index.load(BM25_DIR),
    )
