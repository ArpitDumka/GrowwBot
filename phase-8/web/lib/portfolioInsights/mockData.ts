import type { FundSnapshot } from "@/lib/marketInsights/types";
import type {
  AssetClass,
  PortfolioFactRow,
  PortfolioHolding,
  PortfolioSummary,
  RadarSeries,
  ScatterPoint,
  TreemapNode,
} from "./types";

export const PORTFOLIO_DISCLAIMER =
  "Facts-only portfolio breakdown. No investment advice, recommendations, or allocation suggestions. Weights are illustrative; scheme metrics sync from the daily corpus.";

/** Fallback portfolio weights (also in phase-8/config/portfolio_weights.yaml). */
export const PORTFOLIO_HOLDINGS: PortfolioHolding[] = [
  { fundId: "flexicap", weightPct: 22, assetClass: "Equity" },
  { fundId: "midcap", weightPct: 18, assetClass: "Equity" },
  { fundId: "elss", weightPct: 15, assetClass: "Equity" },
  { fundId: "smallcap", weightPct: 12, assetClass: "Equity" },
  { fundId: "defence", weightPct: 8, assetClass: "Equity" },
  { fundId: "manufacturing", weightPct: 7, assetClass: "Equity" },
  { fundId: "pharma", weightPct: 6, assetClass: "Equity" },
  { fundId: "gold", weightPct: 7, assetClass: "Gold" },
  { fundId: "silver", weightPct: 5, assetClass: "Silver" },
];

export type PortfolioContext = {
  funds: FundSnapshot[];
  holdings: PortfolioHolding[];
};

const THEMATIC_CATEGORIES = new Set(["Thematic", "Sectoral"]);

const RISK_SCORE: Record<string, number> = {
  "Very High": 85,
  High: 65,
  Moderate: 45,
  Low: 25,
};

function fundById(ctx: PortfolioContext, id: string): FundSnapshot {
  const f = ctx.funds.find((x) => x.id === id);
  if (!f) throw new Error(`Unknown fund: ${id}`);
  return f;
}

function volatilityIndex(fund: FundSnapshot): number {
  const r1y = fund.returns["1Y"] ?? 0;
  let base = Math.abs(r1y) * 0.55 + 12;
  if (fund.category.includes("Small")) base += 4;
  if (fund.category === "Commodities") base -= 4;
  return Math.round(Math.min(35, Math.max(10, base)) * 10) / 10;
}

export function portfolioSummary(ctx: PortfolioContext): PortfolioSummary {
  const equityPct = ctx.holdings.filter((h) => h.assetClass === "Equity").reduce((s, h) => s + h.weightPct, 0);
  const goldPct = ctx.holdings.filter((h) => h.assetClass === "Gold").reduce((s, h) => s + h.weightPct, 0);
  const silverPct = ctx.holdings.filter((h) => h.assetClass === "Silver").reduce((s, h) => s + h.weightPct, 0);

  const categories = Array.from(new Set(ctx.holdings.map((h) => fundById(ctx, h.fundId).category)));
  const thematicCount = ctx.holdings.filter((h) =>
    THEMATIC_CATEGORIES.has(fundById(ctx, h.fundId).category)
  ).length;

  return {
    totalFunds: ctx.holdings.length,
    equityPct,
    goldPct,
    silverPct,
    categoryCount: categories.length,
    thematicCount,
    categories,
  };
}

export function allocationDonutData(ctx: PortfolioContext) {
  const summary = portfolioSummary(ctx);
  return [
    { name: "Equity", value: summary.equityPct, fill: "#00D09C" },
    { name: "Gold", value: summary.goldPct, fill: "#F5C542" },
    { name: "Silver", value: summary.silverPct, fill: "#A8B4C4" },
  ];
}

export function portfolioTreemap(ctx: PortfolioContext): TreemapNode {
  const equity = ctx.holdings.filter((h) => h.assetClass === "Equity");
  const gold = ctx.holdings.filter((h) => h.assetClass === "Gold");
  const silver = ctx.holdings.filter((h) => h.assetClass === "Silver");

  const leaf = (h: PortfolioHolding) => ({
    name: fundById(ctx, h.fundId).shortName,
    size: h.weightPct,
  });

  return {
    name: "Portfolio",
    children: [
      { name: "Equity", children: equity.map(leaf) },
      { name: "Commodities", children: [...gold, ...silver].map(leaf) },
    ],
  };
}

export function categoryStackedBarData(ctx: PortfolioContext): Record<string, number | string>[] {
  const byCategory = new Map<string, Record<string, number | string>>();

  for (const h of ctx.holdings) {
    const fund = fundById(ctx, h.fundId);
    const cat = fund.category;
    if (!byCategory.has(cat)) {
      byCategory.set(cat, { category: cat });
    }
    byCategory.get(cat)![fund.shortName] = h.weightPct;
  }

  return Array.from(byCategory.values());
}

export function stackedBarFundKeys(ctx: PortfolioContext): string[] {
  return ctx.holdings.map((h) => fundById(ctx, h.fundId).shortName);
}

export function scatterRiskReturn(ctx: PortfolioContext): ScatterPoint[] {
  return ctx.holdings.map((h) => {
    const fund = fundById(ctx, h.fundId);
    const vol = volatilityIndex(fund);
    return {
      name: fund.shortName,
      risk: vol,
      return1Y: fund.returns["1Y"] ?? 0,
      volatility: vol,
    };
  });
}

export function sectorHeatmap(ctx: PortfolioContext): { sector: string; intensity: number }[] {
  const totals = new Map<string, number>();

  for (const h of ctx.holdings) {
    const fund = fundById(ctx, h.fundId);
    for (const [sector, pct] of Object.entries(fund.sectors)) {
      const weighted = (pct * h.weightPct) / 100;
      totals.set(sector, (totals.get(sector) ?? 0) + weighted);
    }
  }

  return Array.from(totals.entries())
    .map(([sector, intensity]) => ({
      sector,
      intensity: Math.round(intensity * 10) / 10,
    }))
    .sort((a, b) => b.intensity - a.intensity);
}

export function radarComparison(ctx: PortfolioContext): RadarSeries[] {
  const maxAum = Math.max(...ctx.funds.map((f) => f.aumCr), 1);

  return ctx.holdings.map((h) => {
    const fund = fundById(ctx, h.fundId);
    const vol = volatilityIndex(fund);
    return {
      fundId: h.fundId,
      name: fund.shortName,
      metrics: {
        volatility: Math.min(100, vol * 3),
        expenseRatio: Math.min(100, fund.expenseRatio * 40),
        return1Y: Math.min(100, (fund.returns["1Y"] ?? 0) * 2),
        aum: Math.round((fund.aumCr / maxAum) * 100),
        risk: RISK_SCORE[fund.risk] ?? 50,
      },
    };
  });
}

export function radarChartData(series: RadarSeries[]) {
  const keys = [
    { key: "volatility" as const, label: "Volatility" },
    { key: "expenseRatio" as const, label: "Expense" },
    { key: "return1Y" as const, label: "1Y Return" },
    { key: "aum" as const, label: "AUM" },
    { key: "risk" as const, label: "Risk" },
  ];

  return keys.map(({ key, label }) => {
    const row: Record<string, string | number> = { metric: label };
    for (const s of series) {
      row[s.name] = s.metrics[key];
    }
    return row;
  });
}

export function portfolioFactsTable(ctx: PortfolioContext): PortfolioFactRow[] {
  return ctx.holdings.map((h) => {
    const fund = fundById(ctx, h.fundId);
    return {
      fundId: h.fundId,
      name: fund.name,
      category: fund.category,
      expenseRatio: fund.expenseRatio,
      return1Y: fund.returns["1Y"] ?? 0,
      risk: fund.risk,
      benchmark: fund.benchmark,
      assetClass: h.assetClass,
      weightPct: h.weightPct,
    };
  });
}

export type ExposureBreakdown = {
  thematicFunds: { name: string; weightPct: number }[];
  equityAllocationPct: number;
  commodityAllocationPct: number;
  categoryDistribution: { category: string; weightPct: number }[];
};

export function exposureBreakdown(ctx: PortfolioContext): ExposureBreakdown {
  const summary = portfolioSummary(ctx);

  const thematicFunds = ctx.holdings
    .filter((h) => THEMATIC_CATEGORIES.has(fundById(ctx, h.fundId).category))
    .map((h) => ({
      name: fundById(ctx, h.fundId).shortName,
      weightPct: h.weightPct,
    }));

  const catMap = new Map<string, number>();
  for (const h of ctx.holdings) {
    const cat = fundById(ctx, h.fundId).category;
    catMap.set(cat, (catMap.get(cat) ?? 0) + h.weightPct);
  }

  const categoryDistribution = Array.from(catMap.entries())
    .map(([category, weightPct]) => ({ category, weightPct }))
    .sort((a, b) => b.weightPct - a.weightPct);

  return {
    thematicFunds,
    equityAllocationPct: summary.equityPct,
    commodityAllocationPct: summary.goldPct + summary.silverPct,
    categoryDistribution,
  };
}

export const RADAR_COLORS = [
  "#00D09C",
  "#5B8DEF",
  "#F5C542",
  "#E879A9",
  "#A78BFA",
  "#38BDF8",
  "#FB923C",
  "#94A3B8",
  "#4ADE80",
];

export function assetClassLabel(ac: AssetClass): string {
  return ac === "Equity" ? "Equity" : ac;
}

export function toPortfolioContext(
  funds: FundSnapshot[],
  holdings: { fundId: string; weightPct: number; assetClass: string }[]
): PortfolioContext {
  return {
    funds,
    holdings: holdings.map((h) => ({
      fundId: h.fundId,
      weightPct: h.weightPct,
      assetClass: h.assetClass as AssetClass,
    })),
  };
}
