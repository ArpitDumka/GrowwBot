import { ApiError, apiBaseUrl } from "@/lib/api";
import type { InsightsResponse } from "./types";

export async function fetchInsights(base?: string): Promise<InsightsResponse> {
  const r = await fetch(`${base ?? apiBaseUrl()}/api/v1/insights`, {
    cache: "no-store",
    mode: "cors",
  });
  if (!r.ok) {
    throw new ApiError(`Insights failed (${r.status})`, { statusCode: r.status });
  }
  return r.json();
}
