"""Ingestion pipeline.

Phase 1: source registry + aliases + sections config
(`sources.py`, `aliases.py`, `sections.py`, `url_utils.py`).
Phase 2: fetcher + HTML parser (`phase-2/mf_ingest/`; stubs in `fetcher.py`,
`parser_html.py` point there).
Phase 3: §3.1–§3.2 in ``phase-3/mf_clean/`` (``cleaner.py``, ``chunker.py``); stubs in
``cleaner.py`` / ``chunker.py`` here point there. Remaining Phase 3+ field polish / §3.3 TBD.
Phase 4: build_index orchestrator.

See `docs/architecture.md` and `docs/edge-cases/`.
"""
