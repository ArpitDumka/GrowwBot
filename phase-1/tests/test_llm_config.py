"""Phase 7 — Groq LLM config."""

from app.compose.llm_config import load_llm_config


def test_llm_yaml_is_groq():
    cfg = load_llm_config()
    assert cfg.provider == "groq"
    assert cfg.model_id == "llama-3.3-70b-versatile"
    assert cfg.temperature == 0
    assert cfg.api_key_env == "GROQ_API_KEY"
    assert "groq.com" in cfg.base_url
