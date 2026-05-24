export type NavPeriod = "1M" | "6M" | "1Y" | "3Y" | "5Y";

export type FundSnapshot = {
  id: string;
  name: string;
  shortName: string;
  nav: number;
  expenseRatio: number;
  aumCr: number;
  risk: string;
  category: string;
  benchmark: string;
  manager: string;
  lockIn: string | null;
  exitLoad: string;
  objective: string;
  categoryDefinition: string;
  sectors: Record<string, number>;
  returns: { "1Y"?: number; "3Y"?: number; "5Y"?: number };
};

export type NavPoint = { date: string; nav: number };

export type MarketFact = {
  id: string;
  time: string;
  tag: string;
  title: string;
  body: string;
};

export type CompareMetric = "expenseRatio" | "aumCr" | "return1Y";
