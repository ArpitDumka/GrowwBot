"""Phase 10 operational readiness checks."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PHASE10_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PHASE10_ROOT.parent


CHECKS = {
    "active scheduler workflow": REPO_ROOT / ".github" / "workflows" / "corpus-refresh.yml",
    "workflow template": PHASE10_ROOT / "workflows" / "corpus-refresh.yml",
    "CI workflow": REPO_ROOT / ".github" / "workflows" / "ci-tests.yml",
    "eval workflow": REPO_ROOT / ".github" / "workflows" / "eval.yml",
    "deployment doc": REPO_ROOT / "docs" / "DEPLOY.md",
    "Makefile deploy target": REPO_ROOT / "Makefile",
    "phase-10 verify script": PHASE10_ROOT / "scripts" / "verify_phase10.ps1",
    "phase-10 deploy script": PHASE10_ROOT / "scripts" / "deploy.ps1",
    "observability doc": PHASE10_ROOT / "observability.md",
    "security doc": PHASE10_ROOT / "security.md",
    "phase-10 runbook": PHASE10_ROOT / "runbooks" / "README.md",
    "deploy runbook": PHASE10_ROOT / "runbooks" / "deploy.md",
    "stale source runbook": PHASE10_ROOT / "runbooks" / "stale-source.md",
    "llm outage runbook": PHASE10_ROOT / "runbooks" / "llm-outage.md",
    "vector corruption runbook": PHASE10_ROOT / "runbooks" / "vector-store-corruption.md",
    "inaccurate answer runbook": PHASE10_ROOT / "runbooks" / "inaccurate-answer.md",
    "chunks corpus": REPO_ROOT / "phase-3" / "data" / "chunks.jsonl",
    "index manifest": REPO_ROOT / "phase-4" / "data" / "index" / "index_manifest.json",
    "chroma index": REPO_ROOT / "phase-4" / "data" / "index" / "chroma",
    "bm25 index": REPO_ROOT / "phase-4" / "data" / "index" / "bm25",
}


def run_checks() -> list[str]:
    missing: list[str] = []
    for label, path in CHECKS.items():
        if not path.exists():
            missing.append(f"{label}: {path.relative_to(REPO_ROOT)}")
    return missing


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mf-phase10-check")
    parser.parse_args(argv)
    missing = run_checks()
    if missing:
        print("Phase 10 readiness failed:", file=sys.stderr)
        for item in missing:
            print(f"  - missing {item}", file=sys.stderr)
        return 1
    print("OK: Phase 10 operational files are present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

