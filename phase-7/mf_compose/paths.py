"""Repository-relative paths (Phase 7 package lives in ``phase-7/``)."""

from __future__ import annotations

from pathlib import Path

PHASE7_ROOT: Path = Path(__file__).resolve().parent.parent
REPO_ROOT: Path = PHASE7_ROOT.parent
PHASE1_ROOT: Path = REPO_ROOT / "phase-1"
PHASE4_ROOT: Path = REPO_ROOT / "phase-4"
PHASE5_ROOT: Path = REPO_ROOT / "phase-5"
PHASE6_ROOT: Path = REPO_ROOT / "phase-6"
CONFIG_DIR: Path = PHASE7_ROOT / "config"
LLM_YAML: Path = PHASE1_ROOT / "config" / "llm.yaml"
BANNED_TOKENS_YAML: Path = CONFIG_DIR / "banned_tokens.yaml"
ENV_FILE: Path = REPO_ROOT / ".env"
