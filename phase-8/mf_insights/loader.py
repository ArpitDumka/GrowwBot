"""Load insights JSON for the API."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from mf_insights.builder import build_insights_payload, write_insights
from mf_insights.paths import CHUNKS_JSONL, INSIGHTS_JSON


@lru_cache(maxsize=1)
def load_insights(*, rebuild: bool = False) -> dict[str, Any]:
    """Return insights payload from committed JSON, rebuilding from corpus if needed."""
    if rebuild or not INSIGHTS_JSON.is_file():
        if CHUNKS_JSONL.is_file():
            return write_insights(INSIGHTS_JSON)
        return build_insights_payload()

    try:
        data = json.loads(INSIGHTS_JSON.read_text(encoding="utf-8"))
        if data.get("funds"):
            return data
    except (json.JSONDecodeError, OSError):
        pass

    if CHUNKS_JSONL.is_file():
        return write_insights(INSIGHTS_JSON)
    return build_insights_payload()
