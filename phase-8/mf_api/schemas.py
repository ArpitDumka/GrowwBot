"""Pydantic request/response models (POST /chat — edge 8.12)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User question (sent in POST body only).")


class ChatResponse(BaseModel):
    trace_id: str
    outcome: Literal["ANSWERED", "REFUSED", "NOT_FOUND", "ERROR"]
    answer: str
    citation_url: str | None = None
    last_updated: str | None = None
    chunk_id: str | None = None
    disclaimer: str
    used_llm: bool = False


class BootstrapResponse(BaseModel):
    title: str
    title_suffix: str
    disclaimer: str
    ephemeral_hint: str
    welcome_message: str = ""
    input_placeholder: str = ""
    client_timeout_hint_seconds: int
    sample_questions: list[dict[str, str]]


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    version: str
