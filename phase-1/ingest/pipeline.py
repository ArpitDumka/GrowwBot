"""End-to-end RAG corpus build: ingest (Phase 2) -> chunk (Phase 3) -> embed (Phase 4).

See ``docs/architecture.md`` sections 3-4 and ``scripts/build_corpus.ps1``.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PHASE2 = REPO_ROOT / "phase-2"
PHASE3 = REPO_ROOT / "phase-3"
PHASE4 = REPO_ROOT / "phase-4"


def _run(cmd: list[str], *, cwd: Path) -> None:
    print(f"\n>> {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, cwd=str(cwd), check=True)


def build_corpus(
    *,
    skip_ingest: bool = False,
    skip_index: bool = False,
    test_embedder: bool = False,
    ingest_strict: bool = True,
) -> int:
    """Run mf-ingest, mf-chunk, mf-build-index (+ verify) in order."""
    if not skip_ingest:
        ingest_cmd = ["mf-ingest"]
        if not ingest_strict:
            ingest_cmd.append("--no-strict")
        _run(ingest_cmd, cwd=PHASE2)

    _run(["mf-chunk", "--summary"], cwd=PHASE3)

    if not skip_index:
        index_cmd = ["mf-build-index"]
        if test_embedder:
            index_cmd.append("--test-embedder")
        _run(index_cmd, cwd=PHASE4)
        _run(
            ["mf-build-index", "export", "-o", "data/index/embeddings.parquet"],
            cwd=PHASE4,
        )
        verify_cmd = ["mf-build-index", "verify"]
        if test_embedder:
            verify_cmd.append("--test-embedder")
        _run(verify_cmd, cwd=PHASE4)

    chunks_path = PHASE3 / "data" / "chunks.jsonl"
    manifest_path = PHASE4 / "data" / "index" / "index_manifest.json"
    print("\n=== Corpus build complete ===")
    print(f"  chunks:   {chunks_path}")
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        print(
            f"  index:    {manifest_path} "
            f"({manifest.get('num_chunks')} chunks, {manifest.get('embedding_model')})"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="python -m ingest.pipeline",
        description="Build RAG corpus: Phase 2 ingest -> Phase 3 chunk -> Phase 4 embed.",
    )
    p.add_argument("--skip-ingest", action="store_true", help="Use existing phase-2/data/processed/")
    p.add_argument("--skip-index", action="store_true", help="Chunk only (no embedding)")
    p.add_argument(
        "--no-strict",
        action="store_true",
        help="Pass --no-strict to mf-ingest (allow partial ingest failures)",
    )
    p.add_argument(
        "--test-embedder",
        action="store_true",
        help="Hashing embedder (no HuggingFace download; for CI)",
    )
    args = p.parse_args(argv)
    return build_corpus(
        skip_ingest=args.skip_ingest,
        skip_index=args.skip_index,
        test_embedder=args.test_embedder,
        ingest_strict=not args.no_strict,
    )


if __name__ == "__main__":
    raise SystemExit(main())
