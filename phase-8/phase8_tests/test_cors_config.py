"""CORS config supports Vercel preview/production origins."""

import os

from mf_api.config import load_api_config


def test_cors_vercel_regex_configured() -> None:
    cfg = load_api_config()
    assert cfg.cors_origin_regex is not None
    assert "vercel" in cfg.cors_origin_regex
    assert "localhost" in cfg.cors_origin_regex


def test_cors_allows_local_next_ports() -> None:
    cfg = load_api_config()
    assert "http://127.0.0.1:3001" in cfg.cors_origins


def test_cors_extra_origins_from_env(monkeypatch) -> None:
    monkeypatch.setenv("CORS_EXTRA_ORIGINS", "https://mf-faq.vercel.app,https://custom.example")
    load_api_config.cache_clear()
    try:
        cfg = load_api_config()
        assert "https://mf-faq.vercel.app" in cfg.cors_origins
        assert "https://custom.example" in cfg.cors_origins
    finally:
        load_api_config.cache_clear()
