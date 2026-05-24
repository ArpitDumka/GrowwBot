export type AppView = "chat" | "market" | "portfolio";

export const INSIGHT_VIEWS = {
  market: "market",
  portfolio: "portfolio",
} as const satisfies Record<string, AppView>;
