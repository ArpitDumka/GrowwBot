"""Export chunk_id ↔ embedding (+ metadata) to Parquet for inspection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mf_index.build_index import _load_manifest
from mf_index.paths import CHROMA_DIR, INDEX_ROOT, MANIFEST_PATH
from mf_index.vector_store import ChromaVectorStore

DEFAULT_PARQUET = INDEX_ROOT / "embeddings.parquet"


def export_embeddings_parquet(
    output_path: Path = DEFAULT_PARQUET,
    *,
    chroma_dir: Path | None = None,
) -> Path:
    """Write one row per chunk: ``chunk_id``, ``embedding`` (float list), metadata columns."""
    if not MANIFEST_PATH.is_file():
        raise FileNotFoundError(f"index not built; missing {MANIFEST_PATH}")

    manifest = _load_manifest() or {}
    vs = ChromaVectorStore(persist_dir=str(chroma_dir or CHROMA_DIR))
    raw = vs.get_all(include_embeddings=True)

    ids: list[str] = list(raw.get("ids") or [])
    if not ids:
        raise ValueError("Chroma collection is empty")

    embeddings_raw = raw.get("embeddings")
    embeddings: list = list(embeddings_raw) if embeddings_raw is not None else []
    metadatas: list[dict[str, Any]] = list(raw.get("metadatas") or [])
    documents: list[str] = list(raw.get("documents") or [])

    rows: list[dict[str, Any]] = []
    for i, chunk_id in enumerate(ids):
        meta = metadatas[i] if i < len(metadatas) else {}
        emb = embeddings[i] if i < len(embeddings) else []
        emb_list = [float(x) for x in emb]
        rows.append(
            {
                "chunk_id": chunk_id,
                "source_id": meta.get("source_id", ""),
                "scheme": meta.get("scheme", ""),
                "category": meta.get("category", ""),
                "section": meta.get("section", ""),
                "doc_type": meta.get("doc_type", ""),
                "last_updated": meta.get("last_updated", ""),
                "fields_detected": meta.get("fields_detected", ""),
                "url": meta.get("url", ""),
                "embedding_model": manifest.get("embedding_model", ""),
                "embedding_dim": int(manifest.get("dimension", len(emb_list))),
                "embedding": emb_list,
                "text_preview": (documents[i][:500] if i < len(documents) else ""),
            }
        )

    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as e:
        raise ImportError(
            "Parquet export requires pyarrow: pip install pyarrow"
        ) from e

    table = pa.Table.from_pylist(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, output_path, compression="zstd")
    return output_path


def export_embeddings_jsonl(
    output_path: Path,
    *,
    chroma_dir: Path | None = None,
    include_full_text: bool = False,
) -> Path:
    """Same data as Parquet but JSONL (one object per line; large)."""
    if not MANIFEST_PATH.is_file():
        raise FileNotFoundError(f"index not built; missing {MANIFEST_PATH}")

    manifest = _load_manifest() or {}
    vs = ChromaVectorStore(persist_dir=str(chroma_dir or CHROMA_DIR))
    raw = vs.get_all(include_embeddings=True)
    ids = list(raw.get("ids") or [])
    embeddings_raw = raw.get("embeddings")
    embeddings: list = list(embeddings_raw) if embeddings_raw is not None else []
    metadatas = list(raw.get("metadatas") or [])
    documents = list(raw.get("documents") or [])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        for i, chunk_id in enumerate(ids):
            meta = metadatas[i] if i < len(metadatas) else {}
            emb = embeddings[i] if i < len(embeddings) else []
            rec = {
                "chunk_id": chunk_id,
                **meta,
                "embedding_model": manifest.get("embedding_model"),
                "embedding_dim": manifest.get("dimension"),
                "embedding": [float(x) for x in emb],
            }
            if include_full_text and i < len(documents):
                rec["text"] = documents[i]
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return output_path
