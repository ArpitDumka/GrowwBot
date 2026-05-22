"""Repository-relative paths (Phase 5 package lives in ``phase-5/``)."""

from __future__ import annotations

from pathlib import Path

PHASE5_ROOT: Path = Path(__file__).resolve().parent.parent
REPO_ROOT: Path = PHASE5_ROOT.parent
PHASE1_ROOT: Path = REPO_ROOT / "phase-1"
CONFIG_DIR: Path = PHASE5_ROOT / "config"

PII_PATTERNS_YAML: Path = CONFIG_DIR / "pii_patterns.yaml"
INJECTION_PATTERNS_YAML: Path = CONFIG_DIR / "injection_patterns.yaml"
ADVISORY_PATTERNS_YAML: Path = CONFIG_DIR / "advisory_patterns.yaml"
FIELD_SYNONYMS_YAML: Path = CONFIG_DIR / "field_synonyms.yaml"
QUERY_REWRITES_YAML: Path = CONFIG_DIR / "query_rewrites.yaml"
CORPUS_SCOPE_YAML: Path = CONFIG_DIR / "corpus_scope.yaml"

MAX_QUERY_CHARS: int = 2000
TRUNCATE_TO_CHARS: int = 1000
