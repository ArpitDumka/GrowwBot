"""End-to-end Phase 1 verification.

Runs every Phase 1.6 exit criterion that can be checked offline:

- sources.yaml loads and passes all per-row + corpus-level invariants
- aliases.yaml loads and passes all per-row + cross-row invariants
- every scheme in sources.yaml has at least one alias

With ``--with-network``, also runs Phase 2 ``mf-ingest verify`` (robots.txt +
HTTP 200 for each registry URL); requires network and ``phase-2`` on
``PYTHONPATH`` or installed (``pip install -e ../phase-2``).

Returns exit code 0 on success, 1 on any failure.

Usage:
    python scripts/verify_phase1.py
    python scripts/verify_phase1.py --with-network
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = ROOT.parent
PHASE2_ROOT = REPO_ROOT / "phase-2"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ingest.aliases import AliasValidationError, load_aliases  # noqa: E402
from ingest.sections import SectionsConfigError, load_sections  # noqa: E402
from ingest.sources import SourceValidationError, load_sources  # noqa: E402

GREEN = "\033[32m"
RED = "\033[31m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def _ok(label: str, detail: str = "") -> None:
    suffix = f" {DIM}{detail}{RESET}" if detail else ""
    print(f"  {GREEN}PASS{RESET}  {label}{suffix}")


def _fail(label: str, err: Exception) -> None:
    print(f"  {RED}FAIL{RESET}  {label}\n        {err}", file=sys.stderr)


def _run_network_checks() -> int:
    if not PHASE2_ROOT.is_dir():
        print(f"  {RED}FAIL{RESET}  --with-network: missing {PHASE2_ROOT}", file=sys.stderr)
        return 1
    env = os.environ.copy()
    extra = os.pathsep.join([str(PHASE2_ROOT), str(ROOT)])
    env["PYTHONPATH"] = f"{extra}{os.pathsep}{env['PYTHONPATH']}" if env.get("PYTHONPATH") else extra
    cmd = [sys.executable, "-m", "mf_ingest.cli", "verify"]
    try:
        subprocess.run(cmd, cwd=str(PHASE2_ROOT), env=env, check=True)
    except subprocess.CalledProcessError:
        return 1
    _ok("network (robots + HTTP 200)", "mf-ingest verify")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase 1 offline + optional network checks.")
    ap.add_argument(
        "--with-network",
        action="store_true",
        help="Run mf-ingest verify (Phase 2) after offline checks.",
    )
    args = ap.parse_args()

    print(f"\n{BOLD}Phase 1 verification - Mutual Fund FAQ Assistant{RESET}\n")
    failures = 0

    try:
        sources = load_sources()
        _ok(
            "config/sources.yaml",
            f"{len(sources)} entries, {len(sources.categories())} categories",
        )
    except (FileNotFoundError, SourceValidationError, Exception) as e:
        _fail("config/sources.yaml", e)
        return 1

    try:
        load_sections()
        _ok("config/sections.yaml", "canonical keys + synonym lists")
    except (FileNotFoundError, SectionsConfigError, Exception) as e:
        _fail("config/sections.yaml", e)
        failures += 1

    aliases = None
    try:
        aliases = load_aliases(registry=sources)
        _ok(
            "config/aliases.yaml",
            f"{len(aliases.canonicals())} schemes, "
            f"{len(aliases.surface_forms())} aliases",
        )
    except (FileNotFoundError, AliasValidationError, Exception) as e:
        _fail("config/aliases.yaml", e)
        failures += 1

    if aliases is not None:
        try:
            for scheme in sources.schemes():
                assert scheme in aliases.canonicals()
            _ok("every scheme has aliases")
        except AssertionError as e:
            _fail("every scheme has aliases", e)
            failures += 1

    try:
        urls = list(sources.urls())
        assert len(set(urls)) == len(urls)
        _ok("URLs are unique")
    except AssertionError as e:
        _fail("URLs are unique", e)
        failures += 1

    print()
    if failures == 0 and args.with_network:
        net = _run_network_checks()
        if net != 0:
            failures += 1

    print()
    if failures == 0:
        print(f"{GREEN}{BOLD}Phase 1: all checks passed.{RESET}\n")
        print(f"{BOLD}Corpus summary:{RESET}")
        print(f"  AMC        : HDFC Mutual Fund")
        print(f"  schemes    : {len(sources)}")
        print(f"  categories : {', '.join(sources.categories())}")
        print()
        print(f"{BOLD}Schemes:{RESET}")
        for s in sources:
            print(f"  - {s.scheme:<35} [{s.category}]")
        print()
        return 0

    print(f"{RED}{BOLD}Phase 1: {failures} check(s) failed.{RESET}\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
