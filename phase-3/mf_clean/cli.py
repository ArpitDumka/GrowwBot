"""CLI: build chunk JSONL from Phase 2 normalized JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mf_clean.chunk_schema import chunk_model_json_schema
from mf_clean.chunker import chunk_corpus, chunks_to_jsonl
from mf_clean.corpus_stats import summarize_chunk_corpus
from mf_clean.paths import CHUNKS_JSONL, PHASE2_PROCESSED


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="mf-chunk",
        description="Section-aware chunks (Phase 3.2–3.4) from phase-2 processed JSON.",
    )
    p.add_argument(
        "--json-schema",
        action="store_true",
        help="Print Chunk JSON Schema (§3.4) to stdout and exit.",
    )
    p.add_argument(
        "--processed-dir",
        type=Path,
        default=None,
        help=f"Directory of *.json (default: {PHASE2_PROCESSED})",
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=CHUNKS_JSONL,
        help=f"Output JSONL path (default: {CHUNKS_JSONL})",
    )
    p.add_argument(
        "--no-clean",
        action="store_true",
        help="Skip Phase 3.1 clean_text (still reduces holdings top-10).",
    )
    p.add_argument(
        "--no-groww-33",
        action="store_true",
        help="Skip Phase 3.3 Groww UI / mega-menu / footer stripping.",
    )
    p.add_argument(
        "--summary",
        action="store_true",
        help="After chunking, print §3.6 corpus-size JSON (chunk counts vs nominal 60–80).",
    )
    args = p.parse_args(argv)

    if args.json_schema:
        print(json.dumps(chunk_model_json_schema(), indent=2))
        return 0

    proc = args.processed_dir or PHASE2_PROCESSED
    if not proc.is_dir():
        print(f"Missing processed dir: {proc}", file=sys.stderr)
        return 1

    chunks = chunk_corpus(
        proc,
        apply_cleaning=not args.no_clean,
        apply_groww_section_clean=not args.no_groww_33,
    )
    out = args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(chunks_to_jsonl(chunks) + "\n", encoding="utf-8")
    print(f"Wrote {len(chunks)} chunks to {out}")
    if args.summary:
        rep = summarize_chunk_corpus(chunks)
        print(json.dumps(rep.__dict__, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
