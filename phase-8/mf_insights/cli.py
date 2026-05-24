"""CLI: mf-build-insights — build dashboard JSON from corpus chunks."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mf_insights.builder import write_insights
from mf_insights.paths import CHUNKS_JSONL, INSIGHTS_JSON


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mf-build-insights",
        description="Build phase-8/data/insights.json from phase-3/data/chunks.jsonl.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=INSIGHTS_JSON,
        help=f"Output path (default: {INSIGHTS_JSON})",
    )
    parser.add_argument(
        "--chunks",
        type=Path,
        default=CHUNKS_JSONL,
        help="Path to chunks.jsonl",
    )
    args = parser.parse_args(argv)

    if not args.chunks.is_file():
        print(f"Missing chunks file: {args.chunks}", file=sys.stderr)
        return 1

    payload = write_insights(args.output, chunks_path=args.chunks)
    print(f"Wrote {len(payload.get('funds', []))} funds to {args.output}")
    print(f"Corpus last_updated: {payload.get('lastUpdated')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
