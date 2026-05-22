"""Phase 4 tests — sample chunks fixture."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_chunks_path(tmp_path: Path) -> Path:
    src = FIXTURES / "sample_chunks.jsonl"
    dest = tmp_path / "chunks.jsonl"
    dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return dest


@pytest.fixture
def sample_chunks_data() -> list[dict]:
    lines = (FIXTURES / "sample_chunks.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(ln) for ln in lines if ln.strip()]
