"""Repository-relative paths for Phase 2."""

from __future__ import annotations

import sys
from pathlib import Path

# phase-2/mf_ingest/paths.py -> phase-2
PHASE2_ROOT: Path = Path(__file__).resolve().parent.parent
REPO_ROOT: Path = PHASE2_ROOT.parent
PHASE1_ROOT: Path = REPO_ROOT / "phase-1"

SOURCES_YAML: Path = PHASE1_ROOT / "config" / "sources.yaml"
SECTIONS_YAML: Path = PHASE1_ROOT / "config" / "sections.yaml"

RAW_ROOT: Path = PHASE2_ROOT / "data" / "raw"
CACHE_DIR: Path = RAW_ROOT / ".cache"
ETAG_CACHE_PATH: Path = CACHE_DIR / "etags.json"
PROCESSED_ROOT: Path = PHASE2_ROOT / "data" / "processed"
MANIFEST_PATH: Path = PROCESSED_ROOT / "ingest_manifest.json"
MANIFEST_PREV_PATH: Path = PROCESSED_ROOT / "ingest_manifest.prev.json"

USER_AGENT = (
    "Mozilla/5.0 (compatible; MF-FAQ-Ingest/0.1) "
    "MF-FAQ-Assistant/Phase2"
)

MIN_SECTIONS_OK = 2  # header + ≥1 structured block (edge case 2.05)


def ensure_phase1_on_sys_path() -> None:
    """So ``from ingest.sources import load_sources`` works when phase-2 is cwd."""
    p = str(PHASE1_ROOT.resolve())
    if p not in sys.path:
        sys.path.insert(0, p)
