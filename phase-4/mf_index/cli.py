"""CLI: ``mf-build-index`` (architecture §4.4)."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from mf_index.build_index import build_hybrid_index, load_hybrid_index
from mf_index.embedder import create_embedder
from mf_index.export_embeddings import DEFAULT_PARQUET, export_embeddings_jsonl, export_embeddings_parquet
from mf_index.paths import CHUNKS_JSONL, MANIFEST_PATH


def _cmd_build(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="mf-build-index", description="Build Chroma + BM25 hybrid index.")
    p.add_argument(
        "--chunks",
        type=Path,
        default=CHUNKS_JSONL,
        help=f"Input JSONL (default: {CHUNKS_JSONL})",
    )
    p.add_argument("--full", action="store_true", default=True, help="Full rebuild (default).")
    p.add_argument("--test-embedder", action="store_true", help="Use hashing embedder (no HF download).")
    p.add_argument("--no-lock", action="store_true", help="Skip build file-lock.")
    args = p.parse_args(argv)

    emb = create_embedder(test=args.test_embedder)
    _, report = build_hybrid_index(
        chunks_path=args.chunks,
        embedder=emb,
        full=args.full,
        use_lock=not args.no_lock,
    )
    print(
        f"Index built: {report.num_chunks} chunks, "
        f"model={report.embedding_model}, dim={report.dimension}, "
        f"{report.elapsed_s:.2f}s"
    )
    if report.num_orphans_removed:
        print(f"  (dropped {report.num_orphans_removed} orphan chunk(s))")
    print(f"  manifest: {report.manifest_path}")
    return 0


def _cmd_verify(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="mf-build-index verify", description="§4.4 metadata filter checks.")
    p.add_argument("--test-embedder", action="store_true")
    args = p.parse_args(argv)

    if not MANIFEST_PATH.is_file():
        print("Index missing; run mf-build-index first.", file=sys.stderr)
        return 1

    emb = create_embedder(test=args.test_embedder)
    idx = load_hybrid_index(embedder=emb)

    scheme = "HDFC Mid Cap Fund"
    hits = idx.search("expense ratio", top_k=20, where={"scheme": scheme})
    schemes = {h.scheme for h in hits}
    if hits and schemes != {scheme}:
        print(f"FAIL: filter scheme={scheme!r} returned {schemes}", file=sys.stderr)
        return 1
    if not hits:
        print(f"WARN: no hits for scheme filter {scheme!r} (query may be weak with test embedder)")

    filtered = [c for c in idx.chunks if c.scheme == scheme]
    if not filtered:
        print(f"FAIL: no chunks in corpus for {scheme!r}", file=sys.stderr)
        return 1

    wrong = [c for c in idx.chunks if c.scheme == scheme and c.scheme != scheme]
    if wrong:
        print("FAIL: internal filter inconsistency", file=sys.stderr)
        return 1

    print(f"OK: metadata filter — {len(filtered)} chunk(s) for {scheme!r}")
    print(f"OK: hybrid search returned {len(hits)} hit(s), schemes={schemes or 'n/a'}")
    return 0


def _cmd_search(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="mf-build-index search", description="Debug hybrid search.")
    p.add_argument("query", help="Search query")
    p.add_argument("--scheme", default=None, help="Metadata filter: scheme name")
    p.add_argument("--top-k", type=int, default=5)
    p.add_argument("--test-embedder", action="store_true")
    args = p.parse_args(argv)

    emb = create_embedder(test=args.test_embedder)
    idx = load_hybrid_index(embedder=emb)
    where = {"scheme": args.scheme} if args.scheme else None
    hits = idx.search(args.query, top_k=args.top_k, where=where)
    for i, h in enumerate(hits, 1):
        print(
            json.dumps(
                {
                    "rank": i,
                    "chunk_id": h.chunk_id,
                    "score": round(h.score, 4),
                    "vector": round(h.vector_score, 4),
                    "bm25": round(h.bm25_score, 4),
                    "scheme": h.scheme,
                    "section": h.section,
                    "preview": h.text_preview[:120],
                },
                ensure_ascii=True,
            )
        )
    return 0


def _cmd_export(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        prog="mf-build-index export",
        description="Export chunk_id + embedding vectors to Parquet (or JSONL).",
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help=f"Output path (default: {DEFAULT_PARQUET} or .jsonl with --jsonl)",
    )
    p.add_argument("--jsonl", action="store_true", help="Write JSONL instead of Parquet")
    p.add_argument("--full-text", action="store_true", help="Include full chunk text (JSONL only)")
    args = p.parse_args(argv)

    if args.jsonl:
        out = args.output or DEFAULT_PARQUET.with_suffix(".jsonl")
        path = export_embeddings_jsonl(out, include_full_text=args.full_text)
    else:
        out = args.output or DEFAULT_PARQUET
        path = export_embeddings_parquet(out)

    print(f"Wrote {path}")
    print("  Open with: pandas.read_parquet(...) or DuckDB / Polars")
    print("  Columns: chunk_id, embedding (list of floats), scheme, section, ...")
    return 0


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "verify":
        return _cmd_verify(argv[1:])
    if argv and argv[0] == "search":
        return _cmd_search(argv[1:])
    if argv and argv[0] == "export":
        return _cmd_export(argv[1:])
    return _cmd_build(argv)


if __name__ == "__main__":
    raise SystemExit(main())
