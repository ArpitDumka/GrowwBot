"""Repository paths for Phase 9."""

from pathlib import Path

PHASE9_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE9_ROOT.parent
CONFIG_DIR = PHASE9_ROOT / "config"
QA_SET_YAML = CONFIG_DIR / "qa_set.yaml"
TOLERANCES_YAML = CONFIG_DIR / "tolerances.yaml"
TARGETS_YAML = CONFIG_DIR / "targets.yaml"
SOURCES_YAML = REPO_ROOT / "phase-1" / "config" / "sources.yaml"
EVAL_DIR = PHASE9_ROOT / "eval"
REPORT_MD = EVAL_DIR / "report.md"
REPORT_JSON = EVAL_DIR / "report.json"
