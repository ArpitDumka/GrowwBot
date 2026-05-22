"""Phase 4 — Build hybrid index from Phase 3 chunks.

Entry point: ``python -m ingest.build_index`` (architecture §4.4).
Implementation lives in ``phase-4/mf_index/``.
"""

from __future__ import annotations

import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    repo = Path(__file__).resolve().parents[2]
    phase4 = repo / "phase-4"
    p4 = str(phase4.resolve())
    if p4 not in sys.path:
        sys.path.insert(0, p4)
    from mf_index.cli import main as mf_main  # noqa: PLC0415

    return mf_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
