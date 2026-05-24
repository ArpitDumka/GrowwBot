from pathlib import Path

PHASE8_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE8_ROOT.parent
CHUNKS_JSONL = REPO_ROOT / "phase-3" / "data" / "chunks.jsonl"
SOURCES_YAML = REPO_ROOT / "phase-1" / "config" / "sources.yaml"
PORTFOLIO_WEIGHTS_YAML = PHASE8_ROOT / "config" / "portfolio_weights.yaml"
INSIGHTS_JSON = PHASE8_ROOT / "data" / "insights.json"

# Dashboard covers these 9 equity/thematic/commodity schemes (excludes liquid).
DASHBOARD_SOURCE_IDS = frozenset(
    {
        "hdfc_midcap",
        "hdfc_flexicap",
        "hdfc_smallcap",
        "hdfc_elss",
        "hdfc_defence",
        "hdfc_pharma",
        "hdfc_manufacturing",
        "hdfc_gold_fof",
        "hdfc_silver_fof",
    }
)

SHORT_IDS: dict[str, str] = {
    "hdfc_midcap": "midcap",
    "hdfc_flexicap": "flexicap",
    "hdfc_smallcap": "smallcap",
    "hdfc_elss": "elss",
    "hdfc_defence": "defence",
    "hdfc_pharma": "pharma",
    "hdfc_manufacturing": "manufacturing",
    "hdfc_gold_fof": "gold",
    "hdfc_silver_fof": "silver",
}

SHORT_NAMES: dict[str, str] = {
    "hdfc_midcap": "Mid Cap",
    "hdfc_flexicap": "Flexi Cap",
    "hdfc_smallcap": "Small Cap",
    "hdfc_elss": "ELSS",
    "hdfc_defence": "Defence",
    "hdfc_pharma": "Pharma",
    "hdfc_manufacturing": "Manufacturing",
    "hdfc_gold_fof": "Gold FoF",
    "hdfc_silver_fof": "Silver FoF",
}

CATEGORY_DEFINITIONS: dict[str, str] = {
    "Mid Cap": "Mid cap funds invest primarily in 101st–250th ranked companies by market cap on Indian exchanges.",
    "Flexi Cap": "Flexi cap funds may invest across large, mid, and small cap stocks without fixed limits.",
    "Small Cap": "Small cap funds focus on companies ranked below mid-cap indices by market capitalisation.",
    "ELSS": "ELSS funds offer tax deduction under 80C with a minimum 3-year lock-in period.",
    "Thematic": "Thematic funds concentrate on a specific sector or theme rather than broad diversification.",
    "Sectoral": "Sectoral funds invest predominantly in one industry such as healthcare or pharma.",
    "Commodities": "Commodity FoF schemes track domestic metal benchmarks through underlying ETF holdings.",
}
