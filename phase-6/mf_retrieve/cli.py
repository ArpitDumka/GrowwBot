"""CLI: ``mf-retrieve`` (architecture §6)."""

from __future__ import annotations

import argparse
import json
import sys

from mf_guard.models import Outcome
from mf_retrieve.models import RetrievalOutcome
from mf_retrieve.pipeline import ask, load_index
from mf_retrieve.retriever import retrieve


def _print_ask(result) -> int:
    g = result.guard
    print(f"guard: {g.outcome.value} / {g.intent.value}")
    if g.outcome != Outcome.PROCEED:
        if g.message:
            print(f"message: {g.message}")
        return 0
    r = result.retrieval
    if not r:
        print("retrieval: skipped")
        return 0
    print(f"retrieval: {r.outcome.value}")
    if r.message:
        print(f"message: {r.message}")
    if r.chunks:
        c = r.chunks[0]
        print(f"chunk: {c.chunk_id} (section={c.section}, score={c.final_score:.3f})")
        print(f"url: {c.url}")
    if r.low_confidence:
        print("low_confidence: true")
    return 0


def _cmd_ask(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="mf-retrieve ask", description="Guard + retrieve.")
    p.add_argument("query", help="User question.")
    p.add_argument("--json", action="store_true")
    p.add_argument("--test-embedder", action="store_true")
    p.add_argument("--test-reranker", action="store_true", help="Skip HF reranker download.")
    args = p.parse_args(argv)

    result = ask(
        args.query,
        test_embedder=args.test_embedder,
        test_reranker=args.test_reranker,
    )
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=True, indent=2))
        return 0
    return _print_ask(result)


def _cmd_search(argv: list[str]) -> int:
    """Retrieve only (expects guard would PROCEED — runs full ask)."""
    return _cmd_ask(argv)


def _cmd_verify(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="mf-retrieve verify", description="Seed retrieval checks.")
    p.add_argument("--test-embedder", action="store_true")
    p.add_argument("--test-reranker", action="store_true", default=True)
    args = p.parse_args(argv)

    seeds = [
        ("What is the expense ratio of HDFC Mid Cap Fund?", "hdfc_midcap", ("header", "fund_details")),
        ("What is the exit load on HDFC ELSS Tax Saver Fund?", "hdfc_elss", "exit_load_tax"),
        ("Should I invest in HDFC Mid Cap?", None, None),  # refused
    ]
    failed = []
    for q, expect_sid, expect_section in seeds:
        res = ask(q, test_embedder=args.test_embedder, test_reranker=args.test_reranker)
        if expect_sid is None:
            if res.guard.outcome != Outcome.REFUSE:
                failed.append(f"{q!r}: expected guard REFUSE")
            continue
        if res.guard.outcome != Outcome.PROCEED:
            failed.append(f"{q!r}: guard {res.guard.outcome}")
            continue
        if not res.retrieval or res.retrieval.outcome != RetrievalOutcome.FOUND:
            failed.append(f"{q!r}: retrieval {getattr(res.retrieval, 'outcome', None)}")
            continue
        c = res.retrieval.chunks[0]
        if expect_sid not in c.chunk_id:
            failed.append(f"{q!r}: chunk {c.chunk_id} expected source {expect_sid}")
        elif expect_section:
            allowed = (expect_section,) if isinstance(expect_section, str) else expect_section
            if c.section not in allowed:
                failed.append(f"{q!r}: section {c.section} not in {allowed}")

    if failed:
        for f in failed:
            print(f"FAIL: {f}", file=sys.stderr)
        return 1
    print(f"OK: {len(seeds)} seed retrieval checks")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print("Usage: mf-retrieve ask <query> | verify [--test-embedder] [--test-reranker]")
        return 0

    cmd = argv[0]
    rest = argv[1:]
    if cmd == "ask":
        return _cmd_ask(rest)
    if cmd == "search":
        return _cmd_search(rest)
    if cmd == "verify":
        return _cmd_verify(rest)
    return _cmd_ask(argv)


if __name__ == "__main__":
    raise SystemExit(main())
