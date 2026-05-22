"""Bridge Phase 7 ``chat()`` into API responses."""

from __future__ import annotations

import hashlib
import logging
import time
import uuid
from typing import Any

from mf_api.bootstrap import load_bootstrap
from mf_api.schemas import ChatResponse

log = logging.getLogger(__name__)


def _query_hash(query: str) -> str:
    return hashlib.sha256(query.encode("utf-8")).hexdigest()[:16]


def run_chat(
    query: str,
    *,
    trace_id: str | None = None,
    prior_user_query: str | None = None,
    prior_assistant_answer: str | None = None,
    test_embedder: bool = False,
    test_reranker: bool = False,
    llm: Any = None,
) -> tuple[ChatResponse, dict[str, Any]]:
    from mf_compose.pipeline import chat  # noqa: PLC0415
    from mf_guard.follow_up import expand_follow_up  # noqa: PLC0415

    tid = trace_id or str(uuid.uuid4())
    effective_query = expand_follow_up(
        query.strip(),
        prior_user_query=prior_user_query,
        prior_assistant_answer=prior_assistant_answer,
    )
    t0 = time.perf_counter()
    result = chat(
        effective_query,
        test_embedder=test_embedder,
        test_reranker=test_reranker,
        llm=llm,
    )
    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    compose = result.compose
    bootstrap = load_bootstrap()

    response = ChatResponse(
        trace_id=tid,
        outcome=compose.outcome.value,
        answer=compose.text,
        citation_url=compose.citation_url,
        last_updated=compose.last_updated,
        chunk_id=compose.chunk_id,
        disclaimer=bootstrap.disclaimer,
        used_llm=compose.used_llm,
    )
    log_payload = {
        "trace_id": tid,
        "query_hash": _query_hash(effective_query),
        "outcome": compose.outcome.value,
        "latency_ms": elapsed_ms,
        "used_llm": compose.used_llm,
        "chunk_id": compose.chunk_id,
        "guard_violations": compose.guard_violations,
        "log_safe": compose.log_safe,
    }
    log.info("chat %s", log_payload)
    return response, log_payload
