"use client";

import { useCallback, useEffect, useState } from "react";
import { FUNDS as MOCK_FUNDS, MARKET_DISCLAIMER, MARKET_FACTS } from "@/lib/marketInsights/mockData";
import { PORTFOLIO_HOLDINGS as MOCK_HOLDINGS } from "@/lib/portfolioInsights/mockData";
import { fetchInsights } from "./api";
import type { InsightsResponse } from "./types";

const SOURCE_BY_FUND_ID: Record<string, string> = {
  midcap: "hdfc_midcap",
  flexicap: "hdfc_flexicap",
  smallcap: "hdfc_smallcap",
  elss: "hdfc_elss",
  defence: "hdfc_defence",
  pharma: "hdfc_pharma",
  manufacturing: "hdfc_manufacturing",
  gold: "hdfc_gold_fof",
  silver: "hdfc_silver_fof",
};

function fallbackHoldings(): InsightsResponse["portfolioHoldings"] {
  return MOCK_HOLDINGS.map((h) => ({
    ...h,
    sourceId: SOURCE_BY_FUND_ID[h.fundId] ?? h.fundId,
  }));
}

type State = {
  data: InsightsResponse | null;
  loading: boolean;
  error: string | null;
  fromApi: boolean;
};

export function useInsights() {
  const [state, setState] = useState<State>({
    data: null,
    loading: true,
    error: null,
    fromApi: false,
  });

  const reload = useCallback(async () => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const data = await fetchInsights();
      setState({ data, loading: false, error: null, fromApi: true });
    } catch (e) {
      const message = e instanceof Error ? e.message : "Could not load insights";
      setState({
        data: {
          generatedAt: "",
          lastUpdated: "",
          disclaimer: MARKET_DISCLAIMER,
          funds: MOCK_FUNDS,
          portfolioHoldings: fallbackHoldings(),
          marketFacts: MARKET_FACTS,
        },
        loading: false,
        error: message,
        fromApi: false,
      });
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const funds = state.data?.funds ?? MOCK_FUNDS;
  const portfolioHoldings = state.data?.portfolioHoldings ?? fallbackHoldings();
  const marketFacts = state.data?.marketFacts ?? MARKET_FACTS;
  const disclaimer = state.data?.disclaimer ?? MARKET_DISCLAIMER;
  const lastUpdated = state.data?.lastUpdated ?? "";

  return {
    ...state,
    funds,
    portfolioHoldings,
    marketFacts,
    disclaimer,
    lastUpdated,
    reload,
  };
}
