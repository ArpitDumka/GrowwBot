"""Repository-relative paths (Phase 6 package lives in ``phase-6/``)."""

from __future__ import annotations

from pathlib import Path

PHASE6_ROOT: Path = Path(__file__).resolve().parent.parent
REPO_ROOT: Path = PHASE6_ROOT.parent
PHASE4_ROOT: Path = REPO_ROOT / "phase-4"
PHASE5_ROOT: Path = REPO_ROOT / "phase-5"
CONFIG_DIR: Path = PHASE6_ROOT / "config"
RETRIEVAL_YAML: Path = CONFIG_DIR / "retrieval.yaml"
