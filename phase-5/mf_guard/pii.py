"""Phase 5.1 — PII detection and log-safe scrubbing (edges 5.01–5.04, 5.20)."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from mf_guard.config_loader import load_pii_patterns

_PAN_NORMALIZE_RE = re.compile(r"[\s.\-]+")
_AADHAAR_12_RE = re.compile(r"(?<!\d)\d{12}(?!\d)")


@dataclass(frozen=True)
class PiiScanResult:
    detected: bool
    types: tuple[str, ...]


def _normalize_for_pan(text: str) -> str:
    return _PAN_NORMALIZE_RE.sub("", text)


def detect_pii(query: str) -> PiiScanResult:
    """Return detected PII types. PAN checked on normalized text (edge 5.01)."""
    patterns = load_pii_patterns()
    found: list[str] = []

    pan_text = _normalize_for_pan(query)
    # Word boundaries fail after space-stripping (edge 5.01); scan normalized blob.
    if re.search(r"(?i)[A-Z]{5}\d{4}[A-Z]", pan_text):
        found.append("pan")

    for name, pats in patterns.items():
        if name == "pan":
            continue
        for pat in pats:
            if name == "aadhaar_12":
                for m in pat.finditer(query):
                    digits = m.group(0)
                    if len(set(digits)) > 1:
                        found.append(name)
                        break
            elif pat.search(query):
                found.append(name)
                break
        if name in found:
            continue

    return PiiScanResult(detected=bool(found), types=tuple(dict.fromkeys(found)))


def scrub_for_log(text: str) -> str:
    """Redact likely PII before any log line (edge 5.03, 10.10)."""
    out = text
    out = re.sub(r"(?i)\b[A-Z]{5}\d{4}[A-Z]\b", "[REDACTED_PAN]", out)
    out = re.sub(r"\b\d{4}\s\d{4}\s\d{4}\b", "[REDACTED_AADHAAR]", out)
    out = re.sub(r"(?i)\b(?:\+91[\s\-]?)?[6-9]\d{9}\b", "[REDACTED_PHONE]", out)
    out = re.sub(
        r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        "[REDACTED_EMAIL]",
        out,
    )
    out = re.sub(r"(?i)\b[A-Z]{4}0[A-Z0-9]{6}\b", "[REDACTED_IFSC]", out)
    out = re.sub(r"\b(?:\d{4}[\s\-]?){3}\d{4}\b", "[REDACTED_CARD]", out)
    out = re.sub(r"(?i)\b(?:password|passwd|pwd|otp|pin)\s*[:=]\s*\S+", "[REDACTED_SECRET]", out)
    return out


def query_hash(query: str) -> str:
    """SHA-256 of normalized query for structured logs (no raw query storage)."""
    normalized = " ".join(query.split()).casefold()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
