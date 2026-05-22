"""Tests for ``ingest.url_utils``."""

from __future__ import annotations

import pytest

from ingest.url_utils import canonical_url, is_groww_mutual_fund_url


class TestCanonicalUrl:
    def test_lowercases_scheme_and_host(self) -> None:
        assert (
            canonical_url("HTTPS://Groww.IN/mutual-funds/hdfc-mid-cap-fund-direct-growth")
            == "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"
        )

    def test_strips_trailing_slash(self) -> None:
        assert (
            canonical_url("https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth/")
            == "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"
        )

    def test_keeps_root_slash(self) -> None:
        assert canonical_url("https://groww.in/") == "https://groww.in/"

    def test_drops_fragment(self) -> None:
        url = "https://groww.in/mutual-funds/hdfc-liquid-fund-direct-growth#exit-load"
        assert (
            canonical_url(url)
            == "https://groww.in/mutual-funds/hdfc-liquid-fund-direct-growth"
        )

    def test_drops_default_port(self) -> None:
        assert (
            canonical_url("https://groww.in:443/mutual-funds/x")
            == "https://groww.in/mutual-funds/x"
        )

    def test_collapses_multi_slash(self) -> None:
        assert (
            canonical_url("https://groww.in//mutual-funds//hdfc-mid-cap-fund-direct-growth")
            == "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"
        )

    def test_idempotent(self) -> None:
        url = "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"
        assert canonical_url(canonical_url(url)) == canonical_url(url)


class TestIsGrowwMutualFundUrl:
    @pytest.mark.parametrize(
        "url",
        [
            "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
            "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
        ],
    )
    def test_accepts_groww_mf(self, url: str) -> None:
        assert is_groww_mutual_fund_url(url) is True

    @pytest.mark.parametrize(
        "url",
        [
            "http://groww.in/mutual-funds/x",                    # not https
            "https://www.groww.in/mutual-funds/x",               # subdomain not groww.in
            "https://groww.in/stocks/hdfc-bank",                 # not /mutual-funds/
            "https://groww.in/mutual-funds/",                    # empty slug
            "https://example.com/mutual-funds/x",                # wrong host
        ],
    )
    def test_rejects_non_groww_mf(self, url: str) -> None:
        assert is_groww_mutual_fund_url(url) is False
