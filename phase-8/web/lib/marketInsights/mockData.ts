import type { FundSnapshot, MarketFact, NavPeriod, NavPoint } from "./types";

/** Facts-only mock data — illustrative; not live market feeds. */
export const MARKET_DISCLAIMER =
  "Facts-only dashboard. No investment advice, recommendations, or predictions. Data shown is illustrative mock data for UI demonstration.";

export const FUNDS: FundSnapshot[] = [
  {
    id: "midcap",
    name: "HDFC Mid Cap Fund",
    shortName: "Mid Cap",
    nav: 142.38,
    expenseRatio: 0.78,
    aumCr: 68420,
    risk: "Very High",
    category: "Mid Cap",
    benchmark: "NIFTY Midcap 150 TRI",
    manager: "Chirag Setalvad",
    lockIn: null,
    exitLoad: "1% if redeemed within 1 year",
    objective: "Long-term capital appreciation through predominantly mid-cap equity exposure.",
    categoryDefinition: "Mid cap funds invest primarily in 101st–250th ranked companies by market cap on Indian exchanges.",
    sectors: { Financials: 18, Industrials: 16, Consumer: 14, IT: 12, Healthcare: 10, Others: 30 },
    returns: { "1Y": 22.4, "3Y": 18.6, "5Y": 21.2 },
  },
  {
    id: "flexicap",
    name: "HDFC Flexi Cap Fund",
    shortName: "Flexi Cap",
    nav: 1985.42,
    expenseRatio: 0.92,
    aumCr: 52800,
    risk: "Very High",
    category: "Flexi Cap",
    benchmark: "NIFTY 500 TRI",
    manager: "Roshi Jain",
    lockIn: null,
    exitLoad: "1% if redeemed within 1 year",
    objective: "Capital appreciation across market caps with flexible allocation.",
    categoryDefinition: "Flexi cap funds may invest across large, mid, and small cap stocks without fixed limits.",
    sectors: { Financials: 22, IT: 15, Consumer: 13, Energy: 8, Healthcare: 9, Others: 33 },
    returns: { "1Y": 19.8, "3Y": 16.4, "5Y": 18.9 },
  },
  {
    id: "smallcap",
    name: "HDFC Small Cap Fund",
    shortName: "Small Cap",
    nav: 128.76,
    expenseRatio: 0.85,
    aumCr: 31250,
    risk: "Very High",
    category: "Small Cap",
    benchmark: "BSE 250 SmallCap TRI",
    manager: "Chirag Setalvad",
    lockIn: null,
    exitLoad: "1% if redeemed within 1 year",
    objective: "Long-term growth via predominantly small-cap equity securities.",
    categoryDefinition: "Small cap funds focus on companies ranked below mid-cap indices by market capitalisation.",
    sectors: { Industrials: 20, Consumer: 17, Financials: 14, Materials: 12, Healthcare: 8, Others: 29 },
    returns: { "1Y": 28.1, "3Y": 24.3, "5Y": 26.7 },
  },
  {
    id: "elss",
    name: "HDFC ELSS Tax Saver Fund",
    shortName: "ELSS",
    nav: 1124.9,
    expenseRatio: 1.05,
    aumCr: 18600,
    risk: "Very High",
    category: "ELSS",
    benchmark: "NIFTY 500 TRI",
    manager: "Shobhit Mehrotra",
    lockIn: "3 years (statutory)",
    exitLoad: "Nil (ELSS lock-in applies)",
    objective: "Tax-saving equity growth under Section 80C with a mandatory lock-in.",
    categoryDefinition: "ELSS funds offer tax deduction under 80C with a minimum 3-year lock-in period.",
    sectors: { Financials: 24, IT: 14, Consumer: 12, Healthcare: 11, Industrials: 9, Others: 30 },
    returns: { "1Y": 17.2, "3Y": 15.8, "5Y": 17.5 },
  },
  {
    id: "defence",
    name: "HDFC Defence Fund",
    shortName: "Defence",
    nav: 18.64,
    expenseRatio: 0.78,
    aumCr: 4200,
    risk: "Very High",
    category: "Thematic",
    benchmark: "Nifty India Defence TRI",
    manager: "Srinivasan Ramamurthy",
    lockIn: null,
    exitLoad: "1% if redeemed within 1 year",
    objective: "Exposure to companies in the defence and allied sectors.",
    categoryDefinition: "Thematic funds concentrate on a specific sector or theme rather than broad diversification.",
    sectors: { Defence: 72, Aerospace: 12, Engineering: 8, Electronics: 5, Others: 3 },
    returns: { "1Y": 45.2, "3Y": 32.1, "5Y": 28.4 },
  },
  {
    id: "pharma",
    name: "HDFC Pharma & Healthcare Fund",
    shortName: "Pharma",
    nav: 16.28,
    expenseRatio: 1.51,
    aumCr: 2100,
    risk: "Very High",
    category: "Sectoral",
    benchmark: "BSE Healthcare TRI",
    manager: "Srinivasan Ramamurthy",
    lockIn: null,
    exitLoad: "1% if redeemed within 30 days",
    objective: "Capital appreciation through pharma and healthcare sector equities.",
    categoryDefinition: "Sectoral funds invest predominantly in one industry such as healthcare or pharma.",
    sectors: { Pharma: 58, Hospitals: 18, Diagnostics: 12, Biotech: 7, Others: 5 },
    returns: { "1Y": 31.6, "3Y": 19.4, "5Y": 14.2 },
  },
  {
    id: "manufacturing",
    name: "HDFC Manufacturing Fund",
    shortName: "Manufacturing",
    nav: 12.95,
    expenseRatio: 0.83,
    aumCr: 3800,
    risk: "Very High",
    category: "Thematic",
    benchmark: "NIFTY India Manufacturing TRI",
    manager: "Srinivasan Ramamurthy",
    lockIn: null,
    exitLoad: "1% if redeemed within 1 year",
    objective: "Participation in India's manufacturing and industrial growth theme.",
    categoryDefinition: "Manufacturing thematic funds target industrial, capital goods, and allied sectors.",
    sectors: { "Capital Goods": 28, Auto: 22, Industrials: 18, Chemicals: 12, Others: 20 },
    returns: { "1Y": 38.4, "3Y": 26.8, "5Y": 24.1 },
  },
  {
    id: "gold",
    name: "HDFC Gold ETF FoF",
    shortName: "Gold FoF",
    nav: 24.18,
    expenseRatio: 0.21,
    aumCr: 8900,
    risk: "High",
    category: "Commodities",
    benchmark: "Domestic Price of Gold",
    manager: "Bhagyesh Kagalkar",
    lockIn: null,
    exitLoad: "1% if redeemed within 15 days",
    objective: "Returns linked to domestic gold prices via ETF FoF structure.",
    categoryDefinition: "Gold FoF invests in gold ETFs; returns track domestic gold price movements.",
    sectors: { Gold: 98, Cash: 2 },
    returns: { "1Y": 18.9, "3Y": 12.4, "5Y": 11.8 },
  },
  {
    id: "silver",
    name: "HDFC Silver ETF FoF",
    shortName: "Silver FoF",
    nav: 14.72,
    expenseRatio: 0.24,
    aumCr: 1200,
    risk: "Very High",
    category: "Commodities",
    benchmark: "Domestic Price of Silver",
    manager: "Bhagyesh Kagalkar",
    lockIn: null,
    exitLoad: "1% if redeemed within 15 days",
    objective: "Exposure to domestic silver price via ETF fund-of-funds.",
    categoryDefinition: "Silver FoF tracks domestic silver benchmarks through underlying ETF holdings.",
    sectors: { Silver: 97, Cash: 3 },
    returns: { "1Y": 22.3, "3Y": 14.1, "5Y": 13.6 },
  },
];

const PERIOD_DAYS: Record<NavPeriod, number> = {
  "1M": 22,
  "6M": 126,
  "1Y": 252,
  "3Y": 756,
  "5Y": 1260,
};

export function navSeries(fundId: string, period: NavPeriod, anchorNav: number): NavPoint[] {
  const days = PERIOD_DAYS[period];
  const points: NavPoint[] = [];
  const end = new Date("2026-05-24");
  let nav = anchorNav;
  for (let i = days; i >= 0; i -= Math.max(1, Math.floor(days / 40))) {
    const d = new Date(end);
    d.setDate(d.getDate() - i);
    const drift = 1 + (Math.sin(i / 12 + fundId.length) * 0.004 - 0.001);
    nav = i === 0 ? anchorNav : nav / drift;
    points.push({
      date: d.toISOString().slice(0, 10),
      nav: Math.round(nav * 100) / 100,
    });
  }
  return points;
}

export const MARKET_FACTS: MarketFact[] = [
  {
    id: "1",
    time: "24 May 2026 · 09:15 IST",
    tag: "Index",
    title: "NIFTY 50 opened higher in early session",
    body: "Benchmark index recorded a positive opening move. This is an informational market fact, not a forecast.",
  },
  {
    id: "2",
    time: "24 May 2026 · 08:40 IST",
    tag: "Gold",
    title: "Domestic gold reference price updated",
    body: "Gold FoF schemes track domestic gold prices. Past movement does not indicate future performance.",
  },
  {
    id: "3",
    time: "23 May 2026 · 16:20 IST",
    tag: "Sector",
    title: "Defence sector names saw elevated trading volume",
    body: "Sector activity data is reported for informational purposes only.",
  },
  {
    id: "4",
    time: "23 May 2026 · 11:05 IST",
    tag: "Volatility",
    title: "India VIX registered a session change",
    body: "Volatility index readings describe market conditions; they are not trading signals.",
  },
  {
    id: "5",
    time: "22 May 2026 · 14:00 IST",
    tag: "Pharma",
    title: "Healthcare index constituents published fact sheet updates",
    body: "AMC disclosures remain the authoritative source for scheme-level facts.",
  },
  {
    id: "6",
    time: "22 May 2026 · 09:30 IST",
    tag: "Silver",
    title: "Silver reference price movement noted",
    body: "Commodity-linked FoF NAVs may reflect underlying metal price changes with a lag.",
  },
];

export function growthSeries(fundId: string, anchorNav: number): NavPoint[] {
  return navSeries(fundId, "5Y", anchorNav).map((p, i, arr) => ({
    date: p.date,
    nav: Math.round(((p.nav / arr[0].nav) - 1) * 10000) / 100,
  }));
}
