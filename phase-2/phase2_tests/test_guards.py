"""Tests for soft-404 and Cloudflare sniffers."""

from __future__ import annotations

from mf_ingest.cloudflare import is_cloudflare_challenge
from mf_ingest.soft404 import is_soft_404


def test_soft404_title() -> None:
    html = "<html><head><title>Page Not Found</title></head><body></body></html>"
    assert is_soft_404(html) is True


def test_soft404_realish_page() -> None:
    html = "<html><head><title>HDFC Mid Cap</title></head><body><h1>Fund</h1>NAV ₹1</body></html>"
    assert is_soft_404(html) is False


def test_cloudflare_challenge() -> None:
    html = "<html><body>cf-browser-verification</body></html>"
    assert is_cloudflare_challenge(html) is True
