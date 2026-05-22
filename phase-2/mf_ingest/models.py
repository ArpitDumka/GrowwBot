"""Pydantic models for normalized ingest output (architecture §2.2)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class SectionBlock(BaseModel):
    """One logical section of a Groww scheme page."""

    section: str = Field(
        description=(
            "Canonical section id: header, fund_details, exit_load_tax, "
            "minimum_investments, holdings, about, fund_managers, lock_in_banner, performance"
        )
    )
    text: str = Field(min_length=1)


class NormalizedDocument(BaseModel):
    """JSON-serializable document written to ``data/processed/<source_id>.json``."""

    source_id: str
    url: str
    fetched_at: str = Field(
        description="UTC ISO-8601 with Z suffix",
    )
    content_hash: str = Field(description="sha256 of UTF-8 HTML bytes")
    scheme: str
    category: str
    publisher: Literal["Groww"] = "Groww"
    sections: list[SectionBlock]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
