"""Shared pytest fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ingest.aliases import AliasRegistry, load_aliases  # noqa: E402
from ingest.sources import SourceRegistry, load_sources  # noqa: E402


@pytest.fixture(scope="session")
def source_registry() -> SourceRegistry:
    return load_sources()


@pytest.fixture(scope="session")
def alias_registry(source_registry: SourceRegistry) -> AliasRegistry:
    return load_aliases(registry=source_registry)
