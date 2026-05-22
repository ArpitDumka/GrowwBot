"""Build file-lock (edge 4.04)."""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path

EX_TEMPFAIL = 75


@contextmanager
def build_lock(lock_path: Path, *, timeout_s: float = 0.0):
    """Exclusive lock; second concurrent build exits with code 75."""
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import portalocker
    except ImportError:
        portalocker = None  # type: ignore[assignment]

    if portalocker is not None:
        flags = portalocker.LOCK_EX | portalocker.LOCK_NB
        with lock_path.open("a+b") as fh:
            try:
                portalocker.lock(fh, flags)
            except portalocker.exceptions.LockException:
                print(f"Another index build holds {lock_path}", file=sys.stderr)
                raise SystemExit(EX_TEMPFAIL) from None
            try:
                yield
            finally:
                portalocker.unlock(fh)
        return

    # Fallback: best-effort (no cross-process guarantee on all platforms)
    if lock_path.exists():
        print(f"Lock file exists: {lock_path} (install portalocker for robust locking)", file=sys.stderr)
        raise SystemExit(EX_TEMPFAIL)
    lock_path.write_text(str(os.getpid()), encoding="utf-8")
    try:
        yield
    finally:
        lock_path.unlink(missing_ok=True)
