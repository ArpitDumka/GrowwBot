"""§7.2 — Groq LLM settings from ``phase-1/config/llm.yaml``."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from mf_compose.paths import LLM_YAML


@dataclass(frozen=True)
class GroqLLMConfig:
    provider: str
    base_url: str
    api_key_env: str
    model_id: str
    fallback_model_id: str | None
    temperature: float
    max_tokens: int
    top_p: float
    pinned_model_id: str

    def api_key(self) -> str | None:
        return os.environ.get(self.api_key_env)


@lru_cache(maxsize=1)
def load_llm_config(path: Path = LLM_YAML) -> GroqLLMConfig:
    if not path.is_file():
        raise FileNotFoundError(f"llm.yaml not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if raw.get("provider") != "groq":
        raise ValueError(f"llm.yaml provider must be 'groq'; got {raw.get('provider')!r}")
    api = raw.get("api") or {}
    model = raw.get("model") or {}
    gen = raw.get("generation") or {}
    temp = float(gen.get("temperature", 0))
    if temp != 0:
        raise ValueError("temperature must be 0 (edge 7.22)")
    return GroqLLMConfig(
        provider="groq",
        base_url=str(api.get("base_url", "https://api.groq.com")),
        api_key_env=str(api.get("api_key_env", "GROQ_API_KEY")),
        model_id=str(model.get("id", "llama-3.3-70b-versatile")),
        fallback_model_id=model.get("fallback_id"),
        temperature=temp,
        max_tokens=int(gen.get("max_tokens", 220)),
        top_p=float(gen.get("top_p", 1)),
        pinned_model_id=str(raw.get("pinned_model_id", model.get("id", ""))),
    )
