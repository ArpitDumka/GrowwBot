from mf_guard.models import GuardResult, Intent, Outcome, SchemeMatch
from mf_index.hybrid import SearchHit
from mf_index.models import ChunkRecord
from mf_retrieve.config_loader import RetrievalConfig
from mf_retrieve.models import RetrievalOutcome
from mf_retrieve.reranker import create_reranker
from mf_retrieve.retriever import retrieve


class _FakeIndex:
    def __init__(self, chunks: list[ChunkRecord]) -> None:
        self.chunks = chunks
        self._map = {c.chunk_id: c for c in chunks}

    def search(self, query: str, *, top_k: int = 5, where: dict | None = None) -> list[SearchHit]:
        out = []
        for c in self.chunks:
            if where and c.scheme != where.get("scheme"):
                continue
            if c.doc_type == "performance":
                continue
            out.append(
                SearchHit(
                    chunk_id=c.chunk_id,
                    score=0.9 if c.section == "exit_load_tax" else 0.5,
                    vector_score=0.5,
                    bm25_score=0.5,
                    scheme=c.scheme,
                    section=c.section,
                    doc_type=c.doc_type,
                    text_preview=c.text[:80],
                )
            )
        out.sort(key=lambda h: h.score, reverse=True)
        return out[:top_k]


def _guard(**kwargs) -> GuardResult:
    base = dict(
        outcome=Outcome.PROCEED,
        intent=Intent.FACT_QUERY,
        rewritten_query="exit load HDFC ELSS",
        working_query="exit load HDFC ELSS",
        schemes=[
            SchemeMatch(
                canonical="HDFC ELSS Tax Saver Fund",
                source_id="hdfc_elss",
                groww_url="https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
            )
        ],
        field_id="exit_load",
    )
    base.update(kwargs)
    return GuardResult(**base)


def test_retrieve_picks_exit_load_section():
    chunks = [
        ChunkRecord(
            chunk_id="hdfc_elss#header",
            text="header",
            source_id="hdfc_elss",
            url="https://groww.in/x",
            section="header",
            scheme="HDFC ELSS Tax Saver Fund",
            category="ELSS",
            last_updated="2026-05-12",
        ),
        ChunkRecord(
            chunk_id="hdfc_elss#exit_load_tax",
            text="Exit load nil. Tax rules apply.",
            source_id="hdfc_elss",
            url="https://groww.in/x",
            section="exit_load_tax",
            scheme="HDFC ELSS Tax Saver Fund",
            category="ELSS",
            last_updated="2026-05-12",
            fields_detected=["exit_load", "tax"],
        ),
    ]
    cfg = RetrievalConfig(
        tau_hard=0.1,
        tau_soft=0.05,
        field_section_map={"exit_load": ("exit_load_tax",)},
        rerank_top_n=2,
        hybrid_top_k=3,
    )
    r = retrieve(
        _guard(),
        _FakeIndex(chunks),
        cfg=cfg,
        passthrough_rerank=True,
    )
    assert r.outcome == RetrievalOutcome.FOUND
    assert r.chunks[0].section == "exit_load_tax"


def test_nav_field_fast_path_prefers_about_over_header():
    """Groww stores Latest NAV in about; header only has the word NAV in the title."""
    chunks = [
        ChunkRecord(
            chunk_id="hdfc_midcap#header",
            text="HDFC Mid Cap Fund - NAV, Mutual Fund Performance",
            source_id="hdfc_midcap",
            url="https://groww.in/x",
            section="header",
            scheme="HDFC Mid Cap Fund",
            category="Mid Cap",
            last_updated="2026-05-12",
            fields_detected=["holdings", "risk"],
        ),
        ChunkRecord(
            chunk_id="hdfc_midcap#about",
            text="Latest NAV as of 15 May 2026 is Rs 218.42.",
            source_id="hdfc_midcap",
            url="https://groww.in/x",
            section="about",
            scheme="HDFC Mid Cap Fund",
            category="Mid Cap",
            last_updated="2026-05-12",
            fields_detected=["nav", "aum"],
        ),
    ]
    cfg = RetrievalConfig(
        tau_hard=0.1,
        field_section_map={"nav": ("about", "header", "fund_details")},
    )
    r = retrieve(
        _guard(
            rewritten_query="NAV HDFC Mid Cap",
            working_query="NAV HDFC Mid Cap",
            schemes=[
                SchemeMatch(
                    canonical="HDFC Mid Cap Fund",
                    source_id="hdfc_midcap",
                    groww_url="https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
                )
            ],
            field_id="nav",
        ),
        _FakeIndex(chunks),
        cfg=cfg,
        passthrough_rerank=True,
    )
    assert r.outcome == RetrievalOutcome.FOUND
    assert r.chunks[0].chunk_id == "hdfc_midcap#about"
    assert "218.42" in r.chunks[0].text


def test_no_scheme_not_found():
    cfg = RetrievalConfig(tau_hard=0.1)
    r = retrieve(
        GuardResult(outcome=Outcome.PROCEED, intent=Intent.FACT_QUERY, field_id="exit_load"),
        _FakeIndex([]),
        cfg=cfg,
        passthrough_rerank=True,
    )
    assert r.outcome == RetrievalOutcome.NOT_FOUND
