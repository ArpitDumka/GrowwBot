"""Phase 10.2 corpus refresh runner.

Runs the same commands as the scheduled GitHub Actions job, but is safe to execute locally.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path


PHASE10_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PHASE10_ROOT.parent
PHASE2_ROOT = REPO_ROOT / "phase-2"
PHASE3_ROOT = REPO_ROOT / "phase-3"
PHASE4_ROOT = REPO_ROOT / "phase-4"
PHASE8_ROOT = REPO_ROOT / "phase-8"
PROCESSED_DIR = PHASE2_ROOT / "data" / "processed"
CHUNKS_JSONL = PHASE3_ROOT / "data" / "chunks.jsonl"
INDEX_ROOT = PHASE4_ROOT / "data" / "index"
MANIFEST_PATH = INDEX_ROOT / "index_manifest.json"
EMBEDDINGS_PARQUET = INDEX_ROOT / "embeddings.parquet"
INSIGHTS_JSON = PHASE8_ROOT / "data" / "insights.json"
REPORT_PATH = PHASE10_ROOT / "reports" / "last_refresh.json"


@dataclass(frozen=True)
class StepResult:
    name: str
    command: list[str]
    cwd: str
    exit_code: int
    elapsed_s: float


@dataclass(frozen=True)
class RefreshReport:
    status: str
    started_at_epoch: int
    elapsed_s: float
    skip_ingest: bool
    skip_index: bool
    test_embedder: bool
    steps: list[StepResult]
    artifacts: dict[str, str]


def _run_step(name: str, command: list[str], *, cwd: Path, dry_run: bool) -> StepResult:
    print(f"\n=== {name} ===")
    print(f"{cwd}> {' '.join(command)}")
    t0 = time.perf_counter()
    if dry_run:
        return StepResult(name, command, str(cwd), 0, 0.0)

    completed = subprocess.run(command, cwd=str(cwd), check=False)
    elapsed = time.perf_counter() - t0
    if completed.returncode != 0:
        raise subprocess.CalledProcessError(completed.returncode, command)
    return StepResult(name, command, str(cwd), completed.returncode, round(elapsed, 2))


def _artifact_status() -> dict[str, str]:
    return {
        "processed_dir": _present(PROCESSED_DIR),
        "chunks_jsonl": _present(CHUNKS_JSONL),
        "index_manifest": _present(MANIFEST_PATH),
        "index_root": _present(INDEX_ROOT),
        "embeddings_parquet": _present(EMBEDDINGS_PARQUET),
        "insights_json": _present(INSIGHTS_JSON),
    }


def _present(path: Path) -> str:
    if path.exists():
        return str(path.relative_to(REPO_ROOT))
    return "missing"


def write_report(report: RefreshReport, path: Path = REPORT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(report)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\nReport: {path}")


def refresh_corpus(
    *,
    skip_ingest: bool = False,
    skip_index: bool = False,
    no_strict: bool = True,
    test_embedder: bool = False,
    no_export: bool = False,
    dry_run: bool = False,
) -> RefreshReport:
    """Run Phase 10.2 refresh steps once."""
    started = int(time.time())
    t0 = time.perf_counter()
    steps: list[StepResult] = []

    try:
        if not skip_ingest:
            ingest_cmd = ["mf-ingest"]
            if no_strict:
                ingest_cmd.append("--no-strict")
            steps.append(_run_step("Phase 2 ingest", ingest_cmd, cwd=PHASE2_ROOT, dry_run=dry_run))

        steps.append(
            _run_step("Phase 3 chunk", ["mf-chunk", "--summary"], cwd=PHASE3_ROOT, dry_run=dry_run)
        )

        steps.append(
            _run_step(
                "Phase 8 build insights",
                ["mf-build-insights"],
                cwd=PHASE8_ROOT,
                dry_run=dry_run,
            )
        )

        if not skip_index:
            build_cmd = ["mf-build-index"]
            if test_embedder:
                build_cmd.append("--test-embedder")
            steps.append(_run_step("Phase 4 build index", build_cmd, cwd=PHASE4_ROOT, dry_run=dry_run))

            if not no_export:
                export_cmd = ["mf-build-index", "export", "-o", str(EMBEDDINGS_PARQUET)]
                steps.append(
                    _run_step("Phase 4 export embeddings", export_cmd, cwd=PHASE4_ROOT, dry_run=dry_run)
                )

            verify_cmd = ["mf-build-index", "verify"]
            if test_embedder:
                verify_cmd.append("--test-embedder")
            steps.append(_run_step("Phase 4 verify", verify_cmd, cwd=PHASE4_ROOT, dry_run=dry_run))

        status = "dry_run" if dry_run else "ok"
    except subprocess.CalledProcessError as exc:
        status = f"failed:{exc.returncode}"
        report = RefreshReport(
            status=status,
            started_at_epoch=started,
            elapsed_s=round(time.perf_counter() - t0, 2),
            skip_ingest=skip_ingest,
            skip_index=skip_index,
            test_embedder=test_embedder,
            steps=steps,
            artifacts=_artifact_status(),
        )
        write_report(report)
        raise

    report = RefreshReport(
        status=status,
        started_at_epoch=started,
        elapsed_s=round(time.perf_counter() - t0, 2),
        skip_ingest=skip_ingest,
        skip_index=skip_index,
        test_embedder=test_embedder,
        steps=steps,
        artifacts=_artifact_status(),
    )
    write_report(report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mf-corpus-refresh",
        description="Run the Phase 10.2 scheduled corpus refresh pipeline once.",
    )
    parser.add_argument("--skip-ingest", action="store_true", help="Use existing processed JSON")
    parser.add_argument("--skip-index", action="store_true", help="Only run ingest + chunk")
    parser.add_argument("--strict", action="store_true", help="Fail if any Groww URL fails")
    parser.add_argument("--test-embedder", action="store_true", help="Use hashing embedder for local tests")
    parser.add_argument("--no-export", action="store_true", help="Skip embeddings.parquet export")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing them")
    args = parser.parse_args(argv)

    try:
        refresh_corpus(
            skip_ingest=args.skip_ingest,
            skip_index=args.skip_index,
            no_strict=not args.strict,
            test_embedder=args.test_embedder,
            no_export=args.no_export,
            dry_run=args.dry_run,
        )
    except subprocess.CalledProcessError:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
