"""Repository-relative paths (Phase 3 package lives in ``phase-3/``)."""

from __future__ import annotations

from pathlib import Path

PHASE3_ROOT: Path = Path(__file__).resolve().parent.parent
REPO_ROOT: Path = PHASE3_ROOT.parent
PHASE2_PROCESSED: Path = REPO_ROOT / "phase-2" / "data" / "processed"
CHUNKS_JSONL: Path = PHASE3_ROOT / "data" / "chunks.jsonl"
