"""End-to-end ingest: fetch → validate → parse → snapshot + JSON (Phase 2)."""

from __future__ import annotations

import json
import logging
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mf_ingest.cloudflare import is_cloudflare_challenge
from mf_ingest.etag_cache import EtagCache
from mf_ingest.fetcher import GrowwFetcher, build_client
from mf_ingest.parser_html import StructuralBreakError, parse_groww_html, section_count
from mf_ingest.paths import (
    MANIFEST_PATH,
    MANIFEST_PREV_PATH,
    PHASE2_ROOT,
    PROCESSED_ROOT,
    RAW_ROOT,
    ensure_phase1_on_sys_path,
)
from mf_ingest.robots import fetch_robots_txt
from mf_ingest.soft404 import is_soft_404

log = logging.getLogger(__name__)


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)


def _atomic_write_text(path: Path, text: str) -> None:
    _atomic_write_bytes(path, text.encode("utf-8"))


def _latest_snapshot(source_dir: Path) -> Path | None:
    files = list(source_dir.glob("*__*.html"))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def _prune_snapshots(source_dir: Path, keep: int = 7) -> None:
    if not source_dir.is_dir():
        return
    files = sorted(source_dir.glob("*__*.html"), key=lambda p: p.stat().st_mtime, reverse=True)
    for f in files[keep:]:
        try:
            f.unlink()
        except OSError as e:
            log.warning("prune failed %s: %s", f, e)


def _load_prev_manifest() -> dict[str, Any] | None:
    if not MANIFEST_PATH.exists():
        return None
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


@dataclass
class IngestEntry:
    source_id: str
    url: str
    ok: bool
    snapshot_path: str | None = None
    processed_path: str | None = None
    content_hash: str | None = None
    section_count: int = 0
    fetched_at: str | None = None
    skipped_not_modified: bool = False
    error: str | None = None
    legally_blocked: bool = False


@dataclass
class IngestReport:
    entries: list[IngestEntry] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def run_ingest(*, dry_run: bool = False, strict: bool = True) -> IngestReport:
    """Fetch all sources from Phase 1 registry, parse, write artifacts."""
    ensure_phase1_on_sys_path()
    from ingest.sources import load_sources  # noqa: PLC0415

    registry = load_sources()
    prev = _load_prev_manifest()
    prev_by_id: dict[str, dict[str, Any]] = {}
    if prev and "entries" in prev:
        for e in prev["entries"]:
            if isinstance(e, dict) and "source_id" in e:
                prev_by_id[e["source_id"]] = e

    robots_client = build_client()
    try:
        rp = fetch_robots_txt(robots_client)
    finally:
        robots_client.close()

    cache = EtagCache()
    report = IngestReport()

    with GrowwFetcher(robots=rp) as fetcher:
        for src in registry:
            entry = IngestEntry(source_id=src.id, url=src.url, ok=False)
            try:
                cond: dict[str, str] | None = None
                cached = cache.get(src.url)
                if cached:
                    if cached.get("etag"):
                        cond = {"If-None-Match": str(cached["etag"])}
                    elif cached.get("last_modified"):
                        cond = {"If-Modified-Since": str(cached["last_modified"])}

                fr = fetcher.fetch(src.url, conditional_headers=cond)

                if fr.legally_blocked:
                    entry.legally_blocked = True
                    entry.error = fr.error
                    entry.ok = False
                    report.entries.append(entry)
                    report.errors.append(f"{src.id}: {fr.error}")
                    continue

                if not fr.ok:
                    entry.error = fr.error
                    report.entries.append(entry)
                    report.errors.append(f"{src.id}: {fr.error}")
                    continue

                if fr.not_modified:
                    entry.skipped_not_modified = True
                    entry.ok = True
                    prev_e = prev_by_id.get(src.id)
                    if prev_e:
                        entry.snapshot_path = prev_e.get("snapshot_path")
                        entry.processed_path = prev_e.get("processed_path")
                        entry.content_hash = prev_e.get("content_hash")
                        entry.section_count = int(prev_e.get("section_count") or 0)
                        entry.fetched_at = prev_e.get("fetched_at")
                    report.entries.append(entry)
                    log.info("%s: 304 Not Modified — reusing previous artifact", src.id)
                    continue

                assert fr.html is not None and fr.raw_bytes is not None

                if is_cloudflare_challenge(fr.html):
                    raise RuntimeError("Cloudflare challenge HTML (edge case 2.04)")

                if is_soft_404(fr.html):
                    raise RuntimeError("soft 404 / missing scheme content (edge case 2.03)")

                prev_sc = None
                if prev_by_id.get(src.id):
                    prev_sc = int(prev_by_id[src.id].get("section_count") or 0)

                doc = parse_groww_html(
                    html=fr.html,
                    raw_bytes=fr.raw_bytes,
                    source_id=src.id,
                    url=src.url,
                    scheme=src.scheme,
                    category=src.category,
                )
                sc = section_count(doc)
                if prev_sc and sc < max(1, int(prev_sc * 0.5)):
                    raise StructuralBreakError(
                        f"section count dropped {prev_sc} -> {sc} (>50% loss vs previous run)"
                    )

                entry.section_count = sc
                entry.content_hash = doc.content_hash
                entry.fetched_at = doc.fetched_at

                day = doc.fetched_at[:10].replace("Z", "")
                snap_name = f"{day}__{doc.content_hash[:16]}.html"
                snap_path = RAW_ROOT / src.id / snap_name
                proc_path = PROCESSED_ROOT / f"{src.id}.json"

                if not dry_run:
                    _atomic_write_bytes(snap_path, fr.raw_bytes)
                    _atomic_write_text(proc_path, doc.model_dump_json(indent=2))
                    _prune_snapshots(RAW_ROOT / src.id)
                    if fr.etag or fr.last_modified:
                        cache.update(
                            src.url,
                            etag=fr.etag,
                            last_modified=fr.last_modified,
                        )

                entry.snapshot_path = str(snap_path.relative_to(PHASE2_ROOT))
                entry.processed_path = str(proc_path.relative_to(PHASE2_ROOT))
                entry.ok = True

            except StructuralBreakError as e:
                entry.error = str(e)
                report.errors.append(f"{src.id}: {e}")
                log.error("%s: %s", src.id, e)
            except Exception as e:  # noqa: BLE001
                entry.error = str(e)
                report.errors.append(f"{src.id}: {e}")
                log.exception("%s: ingest failed", src.id)

            report.entries.append(entry)

    if not dry_run:
        cache.save()
        PROCESSED_ROOT.mkdir(parents=True, exist_ok=True)
        if MANIFEST_PATH.exists():
            shutil.copy2(MANIFEST_PATH, MANIFEST_PREV_PATH)
        manifest = {
            "entries": [e.__dict__ for e in report.entries],
            "errors": report.errors,
        }
        _atomic_write_text(MANIFEST_PATH, json.dumps(manifest, indent=2))

    if strict and report.errors:
        raise RuntimeError(
            "ingest completed with errors:\n  - " + "\n  - ".join(report.errors)
        )

    return report
