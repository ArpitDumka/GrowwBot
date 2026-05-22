import type { ChatMessage, ChatSession } from "./types";

const STORAGE_KEY = "hdfc-mf-faq-sessions-v1";

export function loadSessions(): ChatSession[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as ChatSession[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function saveSessions(sessions: ChatSession[]): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
}

export function newSessionId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export function titleFromQuery(query: string): string {
  const t = query.trim();
  if (t.length <= 42) return t;
  return `${t.slice(0, 39)}…`;
}

export function newSession(firstQuery?: string): ChatSession {
  const now = Date.now();
  return {
    id: newSessionId(),
    title: firstQuery ? titleFromQuery(firstQuery) : "New Chat",
    createdAt: now,
    updatedAt: now,
    messages: [],
  };
}

export function sessionMessages(session: ChatSession): ChatMessage[] {
  return session.messages.map((m) => ({
    id: m.id,
    role: m.role,
    content: m.content,
    traceId: m.traceId,
    error: m.error,
    createdAt: m.createdAt,
  }));
}
