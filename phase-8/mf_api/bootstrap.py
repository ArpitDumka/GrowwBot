"""Bootstrap payload for the UI (§8.1 welcome + sample questions)."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from mf_api.config import load_api_config
from mf_api.paths import SAMPLE_QUESTIONS_YAML, SOURCES_YAML


@dataclass(frozen=True)
class SampleQuestion:
    id: str
    text: str
    scheme_id: str


@dataclass(frozen=True)
class BootstrapPayload:
    title: str
    title_suffix: str
    disclaimer: str
    ephemeral_hint: str
    welcome_message: str
    input_placeholder: str
    sample_questions: tuple[SampleQuestion, ...]
    client_timeout_hint_seconds: int

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "title_suffix": self.title_suffix,
            "disclaimer": self.disclaimer,
            "ephemeral_hint": self.ephemeral_hint,
            "welcome_message": self.welcome_message,
            "input_placeholder": self.input_placeholder,
            "client_timeout_hint_seconds": self.client_timeout_hint_seconds,
            "sample_questions": [
                {"id": q.id, "text": q.text, "scheme_id": q.scheme_id} for q in self.sample_questions
            ],
        }


def _load_source_ids(path: Path = SOURCES_YAML) -> frozenset[str]:
    if not path.is_file():
        raise FileNotFoundError(f"sources.yaml not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    ids = {str(s["id"]) for s in raw.get("sources") or [] if isinstance(s, dict) and s.get("id")}
    if not ids:
        raise ValueError("sources.yaml has no source ids")
    return frozenset(ids)


@lru_cache(maxsize=1)
def load_bootstrap(path: Path = SAMPLE_QUESTIONS_YAML) -> BootstrapPayload:
    if not path.is_file():
        raise FileNotFoundError(f"sample_questions.yaml not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    disclaimer = str(raw.get("disclaimer", "Facts-only. No investment advice."))
    ephemeral = str(
        raw.get(
            "ephemeral_hint",
            "Chats are saved in this browser only. Do not share PAN, Aadhaar, or bank details here.",
        )
    )
    welcome = str(
        raw.get(
            "welcome_message",
            "Ask factual questions about 10 HDFC mutual funds on Groww. Tap a sample question to begin.",
        )
    ).strip()
    placeholder = str(
        raw.get("input_placeholder", "Ask about an HDFC fund — e.g. expense ratio, exit load…")
    ).strip()
    allowed = _load_source_ids()
    questions: list[SampleQuestion] = []
    for item in raw.get("sample_questions") or []:
        if not isinstance(item, dict):
            continue
        sid = str(item.get("scheme_id", ""))
        if sid not in allowed:
            raise ValueError(f"sample question scheme_id {sid!r} not in sources.yaml")
        questions.append(
            SampleQuestion(
                id=str(item["id"]),
                text=str(item["text"]),
                scheme_id=sid,
            )
        )
    if len(questions) < 3:
        raise ValueError("sample_questions.yaml must define at least 3 questions")
    api = load_api_config()
    return BootstrapPayload(
        title=api.title,
        title_suffix="Facts-only",
        disclaimer=disclaimer,
        ephemeral_hint=ephemeral,
        welcome_message=welcome,
        input_placeholder=placeholder,
        sample_questions=tuple(questions),
        client_timeout_hint_seconds=api.client_timeout_hint_seconds,
    )
