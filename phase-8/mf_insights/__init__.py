"""Build and load dashboard insights from the Phase 3 corpus."""

from mf_insights.builder import build_insights_payload
from mf_insights.loader import load_insights

__all__ = ["build_insights_payload", "load_insights"]
