"""§7.2 — Groq chat completions."""

from __future__ import annotations

import logging
from typing import Protocol

from mf_compose.llm_config import GroqLLMConfig

log = logging.getLogger(__name__)


class LLMClient(Protocol):
    def complete(self, messages: list[dict[str, str]], *, cfg: GroqLLMConfig) -> str: ...


class GroqLLMClient:
    def complete(self, messages: list[dict[str, str]], *, cfg: GroqLLMConfig) -> str:
        key = cfg.api_key()
        if not key:
            raise RuntimeError(
                f"{cfg.api_key_env} is not set. Copy .env.example to .env and add your Groq API key."
            )
        from groq import Groq

        client = Groq(api_key=key, base_url=cfg.base_url)
        models = [cfg.model_id]
        if cfg.fallback_model_id:
            models.append(cfg.fallback_model_id)

        last_err: Exception | None = None
        for model in models:
            try:
                resp = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=cfg.temperature,
                    max_tokens=cfg.max_tokens,
                    top_p=cfg.top_p,
                )
                return (resp.choices[0].message.content or "").strip()
            except Exception as e:
                last_err = e
                log.warning("Groq model %s failed: %s", model, e)
        raise RuntimeError(f"Groq completion failed: {last_err}") from last_err


class StubLLMClient:
    """Deterministic client for unit tests (no network)."""

    def __init__(self, response: str) -> None:
        self._response = response

    def complete(self, messages: list[dict[str, str]], *, cfg: GroqLLMConfig) -> str:
        return self._response
