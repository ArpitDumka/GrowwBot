"""CLI: ``mf-eval``."""

from __future__ import annotations

import argparse
import sys

from mf_eval.runner import run_eval
from mf_eval.validator import validate_coverage


def _cmd_run(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="mf-eval run")
    p.add_argument("--mode", choices=("pipeline", "api"), default="pipeline")
    p.add_argument("--api-url", default=None)
    p.add_argument("--test-reranker", action="store_true", default=True)
    p.add_argument("--no-test-reranker", action="store_false", dest="test_reranker")
    p.add_argument("--live-groq", action="store_true", help="Use real Groq (needs GROQ_API_KEY).")
    p.add_argument("--ci", action="store_true", help="Relaxed targets for CI stub mode.")
    p.add_argument("--skip-link-check", action="store_true")
    p.add_argument("--limit", type=int, default=None)
    args = p.parse_args(argv)

    report = run_eval(
        mode=args.mode,
        api_url=args.api_url,
        test_reranker=args.test_reranker,
        live_groq=args.live_groq,
        ci_mode=args.ci,
        skip_link_check=args.skip_link_check,
        limit=args.limit,
    )
    print(f"Eval: {report.passed}/{report.total} passed, targets_met={report.targets_met}")
    print(f"Report: phase-9/eval/report.md")
    return 0 if report.targets_met else 1


def _cmd_validate(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="mf-eval validate")
    args = p.parse_args(argv)
    errors = validate_coverage()
    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        return 1
    print("OK: qa_set.yaml coverage valid")
    return 0


def _cmd_generate(argv: list[str]) -> int:
    from scripts.generate_qa_set import main

    main()
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print("Usage: mf-eval run | validate | generate")
        return 0
    cmd = argv[0]
    rest = argv[1:]
    if cmd == "run":
        return _cmd_run(rest)
    if cmd == "validate":
        return _cmd_validate(rest)
    if cmd == "generate":
        import runpy
        from pathlib import Path

        script = Path(__file__).resolve().parents[1] / "scripts" / "generate_qa_set.py"
        runpy.run_path(str(script), run_name="__main__")
        return 0
    print(f"Unknown command: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
