"""Phase 3.2 — Section-aware chunker (delegates to ``phase-3/mf_clean``)."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_PHASE3 = _REPO / "phase-3"
if str(_PHASE3) not in sys.path:
    sys.path.insert(0, str(_PHASE3))

from mf_clean.chunk_models import Chunk, NormalizedDocument  # noqa: E402
from mf_clean.chunker import (  # noqa: E402
    chunk_corpus,
    chunk_normalized_document,
    chunks_to_jsonl,
)

__all__ = [
    "Chunk",
    "NormalizedDocument",
    "chunk_corpus",
    "chunk_normalized_document",
    "chunks_to_jsonl",
]
