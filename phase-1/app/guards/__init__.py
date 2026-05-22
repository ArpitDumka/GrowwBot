"""Pre- and post-LLM guardrails.

- ``pii``: scrubs PAN/Aadhaar/phone/email/OTP patterns (Phase 5).
- ``intent``: classifies FACT / ADVISORY / PERFORMANCE / COMPARISON / OOS / PII.
- ``output_guard``: enforces <=3 sentences, single citation, allow-listed URL,
  banned-token check, numeric containment (Phase 7).
"""
