"""End-to-end chat: Phases 5 → 6 → 7."""

from __future__ import annotations

from mf_compose.composer import compose_from_ask
from mf_compose.groq_client import LLMClient
from mf_compose.llm_config import GroqLLMConfig
from mf_compose.models import ChatResult
from mf_compose.paths import ENV_FILE, PHASE4_ROOT, PHASE5_ROOT, PHASE6_ROOT


def load_env() -> None:
    try:
        from dotenv import load_dotenv

        if ENV_FILE.is_file():
            load_dotenv(ENV_FILE)
    except ImportError:
        pass


def ensure_paths() -> None:
    import sys

    for root in (PHASE5_ROOT, PHASE6_ROOT, PHASE4_ROOT):
        p = str(root.resolve())
        if p not in sys.path:
            sys.path.insert(0, p)


_INDEX_CACHE: dict[bool, object] = {}


def _cached_index(*, test_embedder: bool):
    """Process-wide cached hybrid index — avoids re-loading the embedder per request."""
    if test_embedder not in _INDEX_CACHE:
        from mf_retrieve.pipeline import load_index  # noqa: PLC0415

        _INDEX_CACHE[test_embedder] = load_index(test_embedder=test_embedder)
    return _INDEX_CACHE[test_embedder]


def chat(
    query: str,
    *,
    test_embedder: bool = False,
    test_reranker: bool = False,
    llm: LLMClient | None = None,
    llm_cfg: GroqLLMConfig | None = None,
) -> ChatResult:
    load_env()
    ensure_paths()
    from mf_retrieve.pipeline import ask  # noqa: PLC0415

    idx = _cached_index(test_embedder=test_embedder)
    ask_result = ask(
        query,
        index=idx,
        test_embedder=test_embedder,
        test_reranker=test_reranker,
    )
    composed = compose_from_ask(ask_result, llm=llm, llm_cfg=llm_cfg)
    return ChatResult(
        query=query,
        compose=composed,
        guard=ask_result.guard,
        retrieval=ask_result.retrieval,
    )
