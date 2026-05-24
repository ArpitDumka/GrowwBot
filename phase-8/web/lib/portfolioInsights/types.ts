export type AssetClass = "Equity" | "Gold" | "Silver";

export type PortfolioHolding = {
  fundId: string;
  weightPct: number;
  assetClass: AssetClass;
};

export type PortfolioSummary = {
  totalFunds: number;
  equityPct: number;
  goldPct: number;
  silverPct: number;
  categoryCount: number;
  thematicCount: number;
  categories: string[];
};

export type PortfolioFactRow = {
  fundId: string;
  name: string;
  category: string;
  expenseRatio: number;
  return1Y: number;
  risk: string;
  benchmark: string;
  assetClass: AssetClass;
  weightPct: number;
};

export type ScatterPoint = {
  name: string;
  risk: number;
  return1Y: number;
  volatility: number;
};

export type RadarSeries = {
  fundId: string;
  name: string;
  metrics: {
    volatility: number;
    expenseRatio: number;
    return1Y: number;
    aum: number;
    risk: number;
  };
};

export type TreemapNode = {
  name: string;
  size?: number;
  children?: TreemapNode[];
};
