"""Pydantic request/response models (POST /chat — edge 8.12)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User question (sent in POST body only).")
    prior_user_query: str | None = Field(
        default=None,
        max_length=500,
        description="Previous user message in this chat (for follow-ups like 'why').",
    )
    prior_assistant_answer: str | None = Field(
        default=None,
        max_length=600,
        description="Previous assistant reply (for follow-up context).",
    )


class ChatResponse(BaseModel):
    trace_id: str
    outcome: Literal["ANSWERED", "REFUSED", "NOT_FOUND", "ERROR"]
    answer: str
    citation_url: str | None = None
    last_updated: str | None = None
    chunk_id: str | None = None
    disclaimer: str
    used_llm: bool = False
    suggested_replies: list[str] | None = Field(
        default=None,
        description="Optional quick-reply chips for the UI (yes/no follow-ups).",
    )


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


class FundInsight(BaseModel):
    id: str
    sourceId: str
    name: str
    shortName: str
    nav: float
    expenseRatio: float
    aumCr: float
    risk: str
    category: str
    benchmark: str
    manager: str
    lockIn: str | None = None
    exitLoad: str
    objective: str
    categoryDefinition: str
    sectors: dict[str, float]
    returns: dict[str, float]
    url: str = ""
    lastUpdated: str = ""


class PortfolioHoldingInsight(BaseModel):
    fundId: str
    sourceId: str
    weightPct: float
    assetClass: str


class MarketFactInsight(BaseModel):
    id: str
    time: str
    tag: str
    title: str
    body: str


class InsightsResponse(BaseModel):
    generatedAt: str
    lastUpdated: str
    disclaimer: str
    funds: list[FundInsight]
    portfolioHoldings: list[PortfolioHoldingInsight]
    marketFacts: list[MarketFactInsight]
