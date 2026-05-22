"""CLI: ``mf-api`` — serve and verify."""

from __future__ import annotations

import argparse
import sys

from mf_api.app import TRACE_HEADER, create_app
from mf_api.config import load_api_config


def create_app_for_serve() -> object:
    """Uvicorn factory entrypoint (``--reload``). Honors MF_API_* env from ``serve``."""
    import os

    test_embedder = os.environ.get("MF_API_TEST_EMBEDDER", "").lower() in ("1", "true", "yes")
    test_reranker = os.environ.get("MF_API_TEST_RERANKER", "").lower() in ("1", "true", "yes")
    return create_app(test_embedder=test_embedder, test_reranker=test_reranker)


def _cmd_serve(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="mf-api serve")
    p.add_argument("--host", default=None)
    p.add_argument("--port", type=int, default=None)
    p.add_argument("--reload", action="store_true")
    p.add_argument("--test-embedder", action="store_true")
    p.add_argument("--test-reranker", action="store_true", help="Skip HF reranker download.")
    args = p.parse_args(argv)

    import os
    from pathlib import Path

    cfg = load_api_config()
    host = args.host or os.environ.get("HOST") or cfg.host
    port = args.port or int(os.environ.get("PORT", str(cfg.port)))

    if args.test_embedder:
        os.environ["MF_API_TEST_EMBEDDER"] = "1"
    if args.test_reranker:
        os.environ["MF_API_TEST_RERANKER"] = "1"

    import uvicorn

    repo = Path(__file__).resolve().parents[2]
    reload_dirs = [
        str(repo / "phase-5"),
        str(repo / "phase-6"),
        str(repo / "phase-7"),
        str(repo / "phase-8" / "mf_api"),
    ]

    if args.reload:
        uvicorn.run(
            "mf_api.cli:create_app_for_serve",
            factory=True,
            host=host,
            port=port,
            reload=True,
            reload_dirs=reload_dirs,
            log_level="info",
        )
    else:
        app = create_app(
            test_embedder=args.test_embedder,
            test_reranker=args.test_reranker,
        )
        uvicorn.run(app, host=host, port=port, log_level="info")
    return 0


def _cmd_verify(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="mf-api verify")
    p.add_argument("--test-reranker", action="store_true", default=True)
    args = p.parse_args(argv)

    from fastapi.testclient import TestClient
    from mf_compose.groq_client import StubLLMClient

    llm = StubLLMClient(
        "Exit load is Nil.\n"
        "Source: https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth\n"
        "Last updated from sources: 2026-05-16"
    )
    app = create_app(test_reranker=args.test_reranker, llm=llm)
    client = TestClient(app)

    boot = client.get("/api/v1/bootstrap")
    if boot.status_code != 200:
        print(f"FAIL bootstrap: {boot.status_code}", file=sys.stderr)
        return 1
    data = boot.json()
    if len(data.get("sample_questions", [])) < 3:
        print("FAIL: expected 3 sample questions", file=sys.stderr)
        return 1
    if "Facts-only" not in data.get("disclaimer", ""):
        print("FAIL: missing disclaimer", file=sys.stderr)
        return 1

    resp = client.post(
        "/api/v1/chat",
        json={"query": "What is the exit load on HDFC ELSS Tax Saver Fund?"},
    )
    if resp.status_code != 200:
        print(f"FAIL chat: {resp.status_code} {resp.text}", file=sys.stderr)
        return 1
    if TRACE_HEADER not in resp.headers:
        print(f"FAIL: missing {TRACE_HEADER} header", file=sys.stderr)
        return 1
    body = resp.json()
    if body.get("outcome") != "ANSWERED":
        print(f"FAIL: outcome={body.get('outcome')}", file=sys.stderr)
        return 1
    if "Source: https://" not in body.get("answer", ""):
        print("FAIL: answer missing citation", file=sys.stderr)
        return 1

    refuse = client.post("/api/v1/chat", json={"query": "Should I invest in HDFC Mid Cap Fund?"})
    if refuse.json().get("outcome") != "REFUSED":
        print(f"FAIL: advisory should REFUSE, got {refuse.json().get('outcome')}", file=sys.stderr)
        return 1

    print("OK: bootstrap + chat + refusal")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print("Usage: mf-api serve | verify")
        print("UI: Next.js frontend lives in phase-8/web/ (run `npm run dev`).")
        return 0
    cmd = argv[0]
    rest = argv[1:]
    if cmd == "serve":
        return _cmd_serve(rest)
    if cmd == "verify":
        return _cmd_verify(rest)
    print(f"Unknown command: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
