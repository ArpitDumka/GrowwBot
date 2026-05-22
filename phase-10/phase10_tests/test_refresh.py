from pathlib import Path

from mf_phase10.refresh import REPO_ROOT, refresh_corpus


def test_dry_run_writes_report():
    report = refresh_corpus(skip_ingest=True, skip_index=True, dry_run=True)
    assert report.status == "dry_run"
    assert len(report.steps) == 1
    assert report.steps[0].name == "Phase 3 chunk"
    assert Path(REPO_ROOT / "phase-10" / "reports" / "last_refresh.json").is_file()

