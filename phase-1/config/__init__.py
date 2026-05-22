"""Configuration directory.

Holds YAML configs only. Python loaders live in `ingest/` (see `ingest.sources`,
`ingest.aliases`). This `__init__.py` lets us reference `config/` as a package
when needed for path resolution.
"""

from pathlib import Path

CONFIG_DIR = Path(__file__).parent

SOURCES_YAML = CONFIG_DIR / "sources.yaml"
ALIASES_YAML = CONFIG_DIR / "aliases.yaml"
SECTIONS_YAML = CONFIG_DIR / "sections.yaml"
LLM_YAML = CONFIG_DIR / "llm.yaml"
