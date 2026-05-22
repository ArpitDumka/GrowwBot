"""Chunk records loaded from Phase 3 JSONL (§3.4 + doc_type)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ChunkRecord(BaseModel):
    chunk_id: str
    text: str
    source_id: str
    url: str
    section: str
    scheme: str
    category: str
    publisher: Literal["Groww"] = "Groww"
    last_updated: str
    fields_detected: list[str] = Field(default_factory=list)
    doc_type: Literal["facts", "performance"] = "facts"

    @field_validator("chunk_id")
    @classmethod
    def chunk_id_format(cls, v: str) -> str:
        if v.count("#") != 1:
            raise ValueError("chunk_id must contain exactly one '#'")
        return v


def load_chunks_jsonl(path: Path) -> list[ChunkRecord]:
    if not path.is_file():
        raise FileNotFoundError(f"chunks file not found: {path}")
    out: list[ChunkRecord] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(ChunkRecord.model_validate_json(line))
        except Exception as e:
            raise ValueError(f"{path}:{line_no}: invalid chunk JSON: {e}") from e
    if not out:
        raise ValueError(f"no chunks in {path}")
    return out


def content_hash(text: str) -> str:
    """Stable hash for incremental rebuild (edge 4.01 / 2.12)."""
    import hashlib

    normalized = re.sub(r"\s+", " ", text.strip())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
