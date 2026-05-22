"""Pydantic models for §3.4 chunks and Phase 2 normalized JSON input."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class SectionBlock(BaseModel):
    section: str
    text: str = Field(min_length=1)


class NormalizedDocument(BaseModel):
    """Compatible with ``phase-2/data/processed/<id>.json``."""

    source_id: str
    url: str
    fetched_at: str
    content_hash: str
    scheme: str
    category: str
    publisher: Literal["Groww"] = "Groww"
    sections: list[SectionBlock]


class Chunk(BaseModel):
    """Retrieval chunk (architecture §3.4 + ``doc_type`` from §3.2)."""

    chunk_id: str
    text: str
    source_id: str
    url: str
    section: str
    scheme: str
    category: str
    publisher: Literal["Groww"] = "Groww"
    last_updated: str = Field(description="YYYY-MM-DD from fetched_at (edge 3.13)")
    fields_detected: list[str] = Field(default_factory=list)
    doc_type: Literal["facts", "performance"] = "facts"

    @field_validator("chunk_id")
    @classmethod
    def chunk_id_format(cls, v: str) -> str:
        if v.count("#") != 1:
            raise ValueError("chunk_id must contain exactly one '#' (source_id#section)")
        left, right = v.split("#", 1)
        if not left.strip() or not right.strip():
            raise ValueError("chunk_id source_id and section parts must be non-empty")
        return v

    @field_validator("last_updated")
    @classmethod
    def last_updated_is_iso_date(cls, v: str) -> str:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
            raise ValueError("last_updated must be YYYY-MM-DD (§3.4)")
        return v

    @field_validator("url")
    @classmethod
    def url_is_http(cls, v: str) -> str:
        if not (v.startswith("https://") or v.startswith("http://")):
            raise ValueError("url must be an http(s) URL (§3.4)")
        return v
