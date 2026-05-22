import type { BootstrapResponse, ChatResponse } from "./types";

export class ApiError extends Error {
  statusCode?: number;
  retryAfter?: string;

  constructor(message: string, opts?: { statusCode?: number; retryAfter?: string }) {
    super(message);
    this.name = "ApiError";
    this.statusCode = opts?.statusCode;
    this.retryAfter = opts?.retryAfter;
  }
}

export function apiBaseUrl(): string {
  const raw = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
  return raw.replace(/\/$/, "");
}

export type HealthCheckResult = {
  ok: boolean;
  /** Browser blocked the request (often CORS or wrong API URL). */
  likelyCors: boolean;
};

export async function checkHealth(base?: string): Promise<HealthCheckResult> {
  const url = `${base ?? apiBaseUrl()}/healthz`;
  try {
    const r = await fetch(url, { cache: "no-store", mode: "cors" });
    if (!r.ok) return { ok: false, likelyCors: false };
    const data = await r.json();
    return { ok: data?.status === "ok", likelyCors: false };
  } catch {
    return { ok: false, likelyCors: true };
  }
}

export async function fetchBootstrap(base?: string): Promise<BootstrapResponse> {
  const r = await fetch(`${base ?? apiBaseUrl()}/api/v1/bootstrap`, { cache: "no-store", mode: "cors" });
  if (!r.ok) {
    throw new ApiError(`Bootstrap failed (${r.status})`, { statusCode: r.status });
  }
  return r.json();
}

export async function postChat(
  query: string,
  opts?: { base?: string; timeoutMs?: number; signal?: AbortSignal }
): Promise<ChatResponse> {
  const base = opts?.base ?? apiBaseUrl();
  const timeoutMs = opts?.timeoutMs ?? 10_000;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  const signal = opts?.signal ?? controller.signal;

  try {
    const r = await fetch(`${base}/api/v1/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
      signal,
      mode: "cors",
    });
    if (r.status === 429) {
      throw new ApiError(
        `Too many requests. Try again in ${r.headers.get("Retry-After") ?? "60"} seconds.`,
        { statusCode: 429, retryAfter: r.headers.get("Retry-After") ?? undefined }
      );
    }
    if (r.status === 422) {
      const body = await r.json().catch(() => ({}));
      throw new ApiError(String(body.detail ?? "Invalid question"), { statusCode: 422 });
    }
    if (!r.ok) {
      throw new ApiError(`Chat failed (${r.status})`, { statusCode: r.status });
    }
    const data: ChatResponse = await r.json();
    const headerTrace = r.headers.get("x-trace-id");
    if (headerTrace && !data.trace_id) {
      data.trace_id = headerTrace;
    }
    return data;
  } catch (e) {
    if (e instanceof ApiError) throw e;
    if (e instanceof DOMException && e.name === "AbortError") {
      throw new ApiError("Request timed out. Please retry.");
    }
    throw new ApiError("Network problem. Please check the API and retry.");
  } finally {
    clearTimeout(timer);
  }
}
