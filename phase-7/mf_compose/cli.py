"""CLI: ``mf-compose`` (architecture §7)."""

from __future__ import annotations

import argparse
import json
import sys

from mf_compose.groq_client import StubLLMClient
from mf_compose.models import ComposeOutcome
from mf_compose.pipeline import chat


def _print_result(result) -> int:
    c = result.compose
    print(f"outcome: {c.outcome.value}")
    print()
    print(c.text)
    if c.chunk_id:
        print()
        print(f"(chunk: {c.chunk_id}, model: {c.model_id or 'n/a'})")
    if c.guard_violations:
        print(f"(guard fixes: {', '.join(c.guard_violations)})")
    return 0


def _cmd_ask(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="mf-compose ask", description="Full RAG answer (5→6→7).")
    p.add_argument("query", help="User question.")
    p.add_argument("--json", action="store_true")
    p.add_argument("--test-embedder", action="store_true")
    p.add_argument("--test-reranker", action="store_true", help="Skip HF reranker download.")
    p.add_argument(
        "--mock-llm",
        action="store_true",
        help="Use stub LLM (no Groq API call) for pipeline smoke test.",
    )
    args = p.parse_args(argv)

    llm = None
    if args.mock_llm:
        llm = StubLLMClient(
            "The exit load on this scheme is Nil.\n"
            "[Source](https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth)\n"
            "Last updated from sources: 2026-05-16"
        )

    result = chat(
        args.query,
        test_embedder=args.test_embedder,
        test_reranker=args.test_reranker,
        llm=llm,
    )
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=True, indent=2))
        return 0
    return _print_result(result)


def _cmd_verify(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="mf-compose verify")
    p.add_argument("--test-embedder", action="store_true")
    p.add_argument("--test-reranker", action="store_true", default=True)
    p.add_argument("--live-groq", action="store_true", help="Call real Groq (needs GROQ_API_KEY).")
    args = p.parse_args(argv)

    llm = None
    if not args.live_groq:
        llm = StubLLMClient(
            "Exit load is Nil for this ELSS scheme.\n"
            "[Source](https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth)\n"
            "Last updated from sources: 2026-05-16"
        )

    r = chat(
        "What is the exit load on HDFC ELSS Tax Saver Fund?",
        test_embedder=args.test_embedder,
        test_reranker=args.test_reranker,
        llm=llm,
    )
    if r.compose.outcome != ComposeOutcome.ANSWERED:
        print(f"FAIL: expected ANSWERED, got {r.compose.outcome}", file=sys.stderr)
        return 1
    if "nil" not in r.compose.text.lower() and "exit load" not in r.compose.text.lower():
        print(f"FAIL: answer missing exit load fact: {r.compose.text!r}", file=sys.stderr)
        return 1
    if "[Source]" not in r.compose.text:
        print("FAIL: missing citation", file=sys.stderr)
        return 1
    print("OK: composed answer with citation")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print("Usage: mf-compose ask <query> | verify [--live-groq] [--mock-llm]")
        return 0

    cmd = argv[0]
    rest = argv[1:]
    if cmd == "ask":
        return _cmd_ask(rest)
    if cmd == "verify":
        return _cmd_verify(rest)
    return _cmd_ask(argv)


if __name__ == "__main__":
    raise SystemExit(main())
