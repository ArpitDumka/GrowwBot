"""Phase 7 — Composer.

Calls **Groq** (``config/llm.yaml`` — OpenAI-compatible API at api.groq.com) with
retrieved context, then runs the output guard. Falls back to ``NOT_FOUND`` when
retrieval is empty (no LLM call, no cost). See ``llm_config.load_llm_config()``.
"""
