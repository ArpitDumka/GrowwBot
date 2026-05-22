"""Repository paths for Phase 8."""

from pathlib import Path

PHASE8_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE8_ROOT.parent
CONFIG_DIR = PHASE8_ROOT / "config"
API_YAML = CONFIG_DIR / "api.yaml"
SAMPLE_QUESTIONS_YAML = CONFIG_DIR / "sample_questions.yaml"
SOURCES_YAML = REPO_ROOT / "phase-1" / "config" / "sources.yaml"
ENV_FILE = REPO_ROOT / ".env"
