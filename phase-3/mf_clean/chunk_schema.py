"""§3.4 chunk schema helpers — JSON Schema + strict documentation-shaped dicts."""

from __future__ import annotations

import json
from typing import Any

from mf_clean.chunk_models import Chunk

# Keys exactly as in ``docs/architecture.md`` §3.4 example (no ``doc_type``).
SPEC_34_KEYS = frozenset(
    {
        "chunk_id",
        "text",
        "source_id",
        "url",
        "section",
        "scheme",
        "category",
        "publisher",
        "last_updated",
        "fields_detected",
    }
)


def chunk_model_json_schema() -> dict[str, Any]:
    """JSON Schema for :class:`Chunk` (includes ``doc_type`` used in §3.2)."""
    return Chunk.model_json_schema()


def chunk_to_spec_dict(chunk: Chunk) -> dict[str, Any]:
    """§3.4 documentation example shape (omits ``doc_type`` / implementation-only fields)."""
    d = chunk.model_dump(mode="json")
    return {k: d[k] for k in SPEC_34_KEYS if k in d}


def dumps_chunk_spec_json(chunk: Chunk, *, indent: int | None = 2) -> str:
    """Serialize a chunk to JSON matching the §3.4 field set."""
    return json.dumps(chunk_to_spec_dict(chunk), ensure_ascii=False, indent=indent)
