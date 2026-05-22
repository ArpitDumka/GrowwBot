"""Phase 10 security check: detect obvious raw-query logging regressions."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


PHASE10_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PHASE10_ROOT.parent

_LOG_QUERY_RE = re.compile(r"\blog\.(?:debug|info|warning|error|exception)\s*\([^)]*\bquery\b", re.I)
_SAFE_ALLOWLIST = {
    "phase-8/mf_api/service.py",  # logs query_hash only; raw query is hashed before payload.
}


def scan(root: Path = REPO_ROOT) -> list[str]:
    findings: list[str] = []
    for path in root.rglob("*.py"):
        rel = path.relative_to(root).as_posix()
        if rel in _SAFE_ALLOWLIST or "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for i, line in enumerate(text.splitlines(), 1):
            if _LOG_QUERY_RE.search(line):
                findings.append(f"{rel}:{i}: possible raw query logging")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mf-log-scan")
    parser.parse_args(argv)
    findings = scan()
    if findings:
        print("Raw-query logging scan failed:", file=sys.stderr)
        for finding in findings:
            print(f"  - {finding}", file=sys.stderr)
        return 1
    print("OK: no obvious raw-query logging patterns found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

