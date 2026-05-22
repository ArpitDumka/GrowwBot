"""CLI entry point for Phase 2 ingest (`mf-ingest`)."""

from __future__ import annotations

import argparse
import logging
import sys


def _cmd_verify(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="mf-ingest verify", description="Robots + HTTP 200 for every Phase 1 URL.")
    p.parse_args(argv)

    from mf_ingest.verify_sources import format_verify_report, verify_registry_urls  # noqa: PLC0415

    ok, errors = verify_registry_urls()
    print(format_verify_report(ok, errors))
    return 0 if ok else 1


def _cmd_ingest(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        prog="mf-ingest",
        description="Fetch + parse all Groww scheme pages (Phase 2 ingest).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and parse only; do not write snapshots, JSON, or manifest.",
    )
    p.add_argument(
        "--no-strict",
        action="store_true",
        help="Do not exit with code 1 when individual URLs fail.",
    )
    args = p.parse_args(argv)

    from mf_ingest.pipeline import run_ingest  # noqa: PLC0415

    strict = not args.no_strict
    try:
        report = run_ingest(dry_run=args.dry_run, strict=strict)
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 1

    ok = sum(1 for e in report.entries if e.ok)
    print(f"Ingest finished: {ok}/{len(report.entries)} sources OK.")
    if report.errors:
        print("Warnings/errors:", file=sys.stderr)
        for line in report.errors:
            print(f"  - {line}", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "verify":
        return _cmd_verify(argv[1:])
    return _cmd_ingest(argv)


if __name__ == "__main__":
    raise SystemExit(main())
