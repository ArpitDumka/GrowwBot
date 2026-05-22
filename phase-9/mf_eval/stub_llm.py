"""Deterministic LLM stub for CI eval (extracts facts from retrieved chunk context)."""

from __future__ import annotations

import re

from mf_compose.llm_config import GroqLLMConfig

_QUERY_RE = re.compile(r"USER QUERY:\s*(.+?)\n\nCONTEXT:", re.S)
_CTX_RE = re.compile(
    r"<<CTX_START>>.*?source:\s*(https://\S+).*?last_updated:\s*(\d{4}-\d{2}-\d{2})\s*\n(.*?)<<CTX_END>>",
    re.S,
)


def _extract_ctx(messages: list[dict[str, str]]) -> tuple[str, str, str, str]:
    user = messages[-1]["content"]
    qm = _QUERY_RE.search(user)
    query = qm.group(1).strip() if qm else ""
    cm = _CTX_RE.search(user)
    if not cm:
        return query, "", "", "2026-05-16"
    url, updated, chunk = cm.group(1), cm.group(2), cm.group(3)
    return query, chunk, url, updated


def _pick(pattern: str, text: str) -> str | None:
    m = re.search(pattern, text, re.I | re.S)
    if not m:
        return None
    for g in m.groups():
        if g and str(g).strip():
            return str(g).strip()
    return m.group(0).strip()


class EvalStubLLM:
    """Synthetic answers from context for repeatable eval without Groq."""

    def complete(self, messages: list[dict[str, str]], *, cfg: GroqLLMConfig) -> str:
        query, chunk, url, updated = _extract_ctx(messages)
        q = query.casefold()
        body = "I could not find that fact in the provided context."

        if re.search(r"expense\s*ratio", q):
            v = _pick(r"Expense ratio \(Direct\):\s*([\d.]+)%", chunk) or _pick(
                r"expense ratio[^%]{0,40}?([\d.]+)\s*%", chunk
            )
            if v:
                body = f"The expense ratio (Direct) is {v}%."
        elif re.search(r"minimum\s*sip|min\.?\s*for\s*sip|min\s+sip", q):
            v = _pick(r"Min\. for SIP\s*₹([\d,]+)", chunk) or _pick(
                r"Minimum SIP Investment is set to ₹([\d,]+)", chunk
            )
            if v:
                body = f"The minimum SIP is ₹{v.replace(',', '')}."
        elif re.search(r"exit\s*load", q):
            if re.search(r"Exit load\s+Nil", chunk, re.I):
                body = "There is no exit load."
            else:
                v = _pick(r"Exit load of\s*([\d.]+)%", chunk)
                if v:
                    body = f"The exit load is {v}% if redeemed within the stated period."
        elif re.search(r"benchmark", q):
            v = _pick(r"Fund benchmark\s+([^\n.;]+)", chunk)
            if v:
                body = f"The benchmark is {v.strip()}."
        elif re.search(r"lock[- ]?in", q):
            if re.search(r"3[- ]?year lock|statutory\s+3[- ]?year", chunk, re.I):
                body = "The lock-in period is 3 years."
        elif re.search(r"\bnav\b|latest\s+nav", q):
            v = _pick(r"Latest NAV is\s*₹([\d,.]+)", chunk)
            if v:
                body = f"The latest NAV is ₹{v}."

        return f"{body}\nSource: {url}\nLast updated from sources: {updated}"
