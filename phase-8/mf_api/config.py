"""Load ``config/api.yaml``."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from mf_api.paths import API_YAML


@dataclass(frozen=True)
class ApiConfig:
    host: str
    port: int
    title: str
    version: str
    cors_origins: tuple[str, ...]
    cors_origin_regex: str | None
    rate_limit_enabled: bool
    rate_limit_rpm: int
    min_query_length: int
    max_query_length: int
    client_timeout_hint_seconds: int


@lru_cache(maxsize=1)
def load_api_config(path: Path = API_YAML) -> ApiConfig:
    if not path.is_file():
        raise FileNotFoundError(f"api.yaml not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    server = raw.get("server") or {}
    cors = raw.get("cors") or {}
    rl = raw.get("rate_limit") or {}
    chat = raw.get("chat") or {}
    origins = list(cors.get("allow_origins") or [])
    extra = os.environ.get("CORS_EXTRA_ORIGINS", "").strip()
    if extra:
        origins.extend(x.strip() for x in extra.split(",") if x.strip())
    regex = cors.get("allow_origin_regex")
    return ApiConfig(
        host=str(server.get("host", "127.0.0.1")),
        port=int(server.get("port", 8000)),
        title=str(server.get("title", "Mutual Fund FAQ Assistant")),
        version=str(server.get("version", "0.1.0")),
        cors_origins=tuple(str(o) for o in origins),
        cors_origin_regex=str(regex) if regex else None,
        rate_limit_enabled=bool(rl.get("enabled", True)),
        rate_limit_rpm=int(rl.get("requests_per_minute", 30)),
        min_query_length=int(chat.get("min_query_length", 3)),
        max_query_length=int(chat.get("max_query_length", 500)),
        client_timeout_hint_seconds=int(chat.get("client_timeout_hint_seconds", 10)),
    )
