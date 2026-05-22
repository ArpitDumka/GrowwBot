"""CLI: ``mf-guard`` (architecture §5)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mf_guard.models import Outcome
from mf_guard.pipeline import process_query
from mf_guard.templates import TEMPLATE_IDS, assert_no_query_interpolation

_FIXTURES = Path(__file__).resolve().parent.parent / "phase5_tests" / "fixtures"


def _cmd_analyze(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="mf-guard analyze", description="Run Phase 5 guard on a query.")
    p.add_argument("query", nargs="?", help="User question (quote if it contains spaces).")
    p.add_argument("--json", action="store_true", help="Emit JSON result.")
    args = p.parse_args(argv)

    if not args.query:
        print("Usage: mf-guard analyze \"<your question>\"", file=sys.stderr)
        return 2

    result = process_query(args.query)
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=True, indent=2))
        return 0

    print(f"outcome: {result.outcome.value}")
    print(f"intent:  {result.intent.value}")
    if result.message:
        print(f"message: {result.message}")
    if result.rewritten_query:
        print(f"rewritten: {result.rewritten_query}")
    if result.schemes:
        s = result.schemes[0]
        print(f"scheme: {s.canonical} ({s.source_id})")
    if result.field_id:
        print(f"field: {result.field_id}")
    print(f"query_hash: {result.query_hash}")
    return 0


def _cmd_verify(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="mf-guard verify", description="§5.3 exit checks.")
    args = p.parse_args(argv)

    advisory_path = _FIXTURES / "advisory_queries.txt"
    if not advisory_path.is_file():
        print(f"FAIL: missing {advisory_path}", file=sys.stderr)
        return 1

    lines = [
        ln.strip()
        for ln in advisory_path.read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]
    failed: list[str] = []
    for q in lines:
        r = process_query(q)
        if r.outcome != Outcome.REFUSE or r.intent.value not in (
            "ADVISORY",
            "MIXED_INTENT",
            "JAILBREAK",
            "COMPARISON",
        ):
            failed.append(f"{q!r} -> {r.outcome.value}/{r.intent.value}")

    for tid in TEMPLATE_IDS:
        msg = _sample_message(tid)
        if msg:
            assert_no_query_interpolation(msg, "ABCDE1234F should I invest in HDFC ELSS?")

    if failed:
        print(f"FAIL: {len(failed)} advisory queries not refused:", file=sys.stderr)
        for f in failed[:10]:
            print(f"  {f}", file=sys.stderr)
        return 1

    print(f"OK: {len(lines)} advisory phrasings refused")
    print(f"OK: {len(TEMPLATE_IDS)} template ids; no query interpolation")
    return 0


def _sample_message(template_id: str) -> str | None:
    from mf_guard import templates as t

    return {
        "ADVISORY": t.ADVISORY,
        "COMPARISON": t.COMPARISON,
        "OUT_OF_SCOPE": t.OUT_OF_SCOPE,
        "UNKNOWN_SCHEME": t.UNKNOWN_SCHEME,
        "PII": t.PII,
        "PERFORMANCE": t.performance_message("https://example.com"),
        "JAILBREAK": t.JAILBREAK,
        "MIXED_INTENT": t.MIXED_INTENT,
        "MULTI_SCHEME": t.MULTI_SCHEME,
        "EMPTY": t.EMPTY,
        "UNSUPPORTED_SCRIPT": t.UNSUPPORTED_SCRIPT,
        "NUMERIC_ONLY": t.NUMERIC_ONLY,
        "NFO": t.NFO,
    }.get(template_id)


def _cmd_demo(argv: list[str]) -> int:
    """Run a small built-in demo set (factual + refusals)."""
    samples = [
        "What is the expense ratio of HDFC Mid Cap Fund?",
        "Should I invest in HDFC ELSS?",
        "My PAN is ABCDE1234F",
        "What is the 3-year return of HDFC Gold ETF FoF?",
        "HDFC mid cap ka expense ratio kya hai?",
    ]
    for q in samples:
        r = process_query(q)
        print(f"\nQ: {q}")
        print(f"   -> {r.outcome.value} / {r.intent.value}")
        if r.rewritten_query and r.outcome == Outcome.PROCEED:
            print(f"   rewrite: {r.rewritten_query}")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(
            "Usage: mf-guard analyze <query> | verify | demo [--json]",
            file=sys.stderr,
        )
        return 0 if not argv else 0

    cmd = argv[0]
    rest = argv[1:]
    if cmd == "analyze":
        return _cmd_analyze(rest if rest else ["--help"])
    if cmd == "verify":
        return _cmd_verify(rest)
    if cmd == "demo":
        return _cmd_demo(rest)
    # Allow `mf-guard "question"` shorthand
    return _cmd_analyze(argv)


if __name__ == "__main__":
    raise SystemExit(main())
