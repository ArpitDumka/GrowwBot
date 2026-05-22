"""Deterministic refusal templates (architecture §5.2).

Templates NEVER interpolate the raw user query (edge 5.17).
"""

from __future__ import annotations

ADVISORY = (
    "I can only share verifiable facts about mutual fund schemes from official sources. "
    "I can't recommend whether to invest. Learn more: "
    "https://www.amfiindia.com/investor-corner/knowledge-center"
)

COMPARISON = (
    "I don't compare schemes or returns. For performance details, please refer to the "
    "official factsheet on Groww."
)

OUT_OF_SCOPE = (
    "This assistant only answers facts about a curated set of mutual fund schemes. "
    "Try one of the example questions shown above."
)

UNKNOWN_SCHEME = (
    "I can only answer about the 10 HDFC schemes in this assistant's corpus "
    "(Mid Cap, Flexi Cap, Small Cap, ELSS, Defence, Pharma & Healthcare, "
    "Manufacturing, Gold ETF FoF, Silver ETF FoF, and Liquid). "
    "Please ask about one of those schemes."
)

PII = (
    "For your privacy and security, please do not share sensitive personal information "
    "like Aadhaar, PAN, bank details, passwords, or OTPs in this chat. "
    "I can help with general HDFC Mutual Fund information — please rephrase without confidential data."
)

PERFORMANCE_PREFIX = (
    "I don't quote returns or performance history from memory. "
    "For the latest returns and charts, see the official Groww scheme page: "
)

JAILBREAK = (
    "I can only answer factual questions about mutual fund schemes from official sources. "
    "I can't follow instructions that change how I work."
)

MIXED_INTENT = (
    "Your question mixes investment advice with a factual part. "
    "Please ask only the factual part on its own (for example, expense ratio of one scheme)."
)

MULTI_SCHEME = (
    "Please ask about one scheme at a time so I can cite a single official source."
)

EMPTY = "Please type a question."

UNSUPPORTED_SCRIPT = (
    "I currently support questions in English (including common Hinglish phrasing). "
    "Please rephrase in English."
)

NUMERIC_ONLY = (
    "I need a full question, not just a number. Try one of the example questions above."
)

URL_IN_QUERY = OUT_OF_SCOPE

NFO = (
    "This assistant covers only the 10 locked HDFC schemes on Groww. "
    "It doesn't track new fund offers (NFOs) or upcoming launches."
)

DOCUMENT_DOWNLOAD = (
    "Downloading account statements or capital-gains reports is outside this assistant's "
    "Groww scheme-page corpus. Use your Groww account or AMC/registrar portal for tax documents."
)

def smalltalk_message(kind: str) -> str:
    """Deterministic conversational reply (delegates to ``conversational`` module)."""
    from mf_guard.conversational import conversational_response

    return conversational_response(kind)


def performance_message(groww_url: str | None) -> str:
    if groww_url:
        return PERFORMANCE_PREFIX + groww_url
    return (
        PERFORMANCE_PREFIX.rstrip(": ")
        + ". Pick one of the example schemes to get the right link."
    )


def comparison_message(groww_url: str | None) -> str:
    if groww_url:
        return COMPARISON + f" {groww_url}"
    return COMPARISON


TEMPLATE_IDS = frozenset(
    {
        "ADVISORY",
        "COMPARISON",
        "OUT_OF_SCOPE",
        "UNKNOWN_SCHEME",
        "PII",
        "PERFORMANCE",
        "JAILBREAK",
        "MIXED_INTENT",
        "MULTI_SCHEME",
        "EMPTY",
        "UNSUPPORTED_SCRIPT",
        "NUMERIC_ONLY",
        "NFO",
        "DOCUMENT_DOWNLOAD",
        "SMALLTALK",
    }
)


def assert_no_query_interpolation(template: str, query: str) -> None:
    """Guard for edge 5.17 — refusal text must not echo user input."""
    if not query or len(query) < 8:
        return
    q = query.strip().lower()
    if len(q) >= 12 and q in template.lower():
        raise ValueError("refusal template must not contain the raw user query")
