import type { FundSnapshot, MarketFact, NavPeriod, NavPoint } from "@/lib/marketInsights/types";

export type PortfolioHoldingInsight = {
  fundId: string;
  sourceId: string;
  weightPct: number;
  assetClass: "Equity" | "Gold" | "Silver";
};

export type InsightsResponse = {
  generatedAt: string;
  lastUpdated: string;
  disclaimer: string;
  funds: FundSnapshot[];
  portfolioHoldings: PortfolioHoldingInsight[];
  marketFacts: MarketFact[];
};

export type { FundSnapshot, MarketFact, NavPeriod, NavPoint };
