"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, apiBaseUrl, checkHealth, fetchBootstrap, postChat } from "@/lib/api";
import {
  loadSessions,
  newSession,
  newSessionId,
  saveSessions,
  sessionMessages,
  titleFromQuery,
} from "@/lib/chatStorage";
import type { BootstrapResponse, ChatMessage, ChatSession, StoredMessage } from "@/lib/types";
import { ChatHeader } from "./ChatHeader";
import { ChatInput } from "./ChatInput";
import { InfoNotice } from "./InfoNotice";
import { LoadingSkeleton } from "./LoadingSkeleton";
import { QuickPrompts } from "./QuickPrompts";
import { MessageBubble } from "./MessageBubble";
import { MobileDrawer } from "./MobileDrawer";
import { Sidebar } from "./Sidebar";

const MARKET_DISCLAIMER =
  "Mutual Fund investments are subject to market risks. Read all scheme related documents carefully.";

const CHAT_HEADER_TITLE = "Groww RAG Chatbot";

/** How long the header shows “Active” after a successful reply before returning to Standby. */
const LLM_ACTIVE_ECHO_MS = 3200;

function msgId(): string {
  return newSessionId();
}

function toStored(m: ChatMessage): StoredMessage {
  return {
    id: m.id,
    role: m.role,
    content: m.content,
    traceId: m.traceId,
    error: m.error,
    createdAt: m.createdAt ?? Date.now(),
  };
}

export function ChatApp() {
  const [boot, setBoot] = useState<BootstrapResponse | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [apiUp, setApiUp] = useState<boolean | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [respondedPulse, setRespondedPulse] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [hydrated, setHydrated] = useState(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const respondedTimerRef = useRef<number | null>(null);

  const timeoutSec = boot?.client_timeout_hint_seconds ?? 45;

  const activeSession = sessions.find((s) => s.id === activeId) ?? null;
  const messages: ChatMessage[] = activeSession ? sessionMessages(activeSession) : [];

  useEffect(() => {
    const stored = loadSessions();
    setSessions(stored);
    if (stored.length > 0) {
      setActiveId(stored[0].id);
    } else {
      const s = newSession();
      setSessions([s]);
      setActiveId(s.id);
    }
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (hydrated) saveSessions(sessions);
  }, [sessions, hydrated]);

  const connectApi = useCallback(async () => {
    setApiUp(null);
    setLoadError(null);
    const health = await checkHealth();
    if (!health.ok) {
      setApiUp(false);
      const base = apiBaseUrl();
      if (health.likelyCors) {
        setLoadError(
          `Browser could not reach ${base}. ` +
            `Restart the backend so the latest CORS config loads: .\\scripts\\run_backend.ps1`
        );
      } else {
        setLoadError(`Cannot reach API at ${base}. Start the backend: .\\scripts\\run_backend.ps1`);
      }
      return;
    }
    setApiUp(true);
    try {
      const data = await fetchBootstrap();
      setBoot(data);
      setLoadError(null);
    } catch (e) {
      setApiUp(false);
      setLoadError(e instanceof ApiError ? e.message : "Failed to load bootstrap");
    }
  }, []);

  useEffect(() => {
    void connectApi();
  }, [connectApi]);

  const clearRespondedPulse = useCallback(() => {
    if (respondedTimerRef.current !== null) {
      window.clearTimeout(respondedTimerRef.current);
      respondedTimerRef.current = null;
    }
    setRespondedPulse(false);
  }, []);

  useEffect(() => {
    clearRespondedPulse();
  }, [activeId, clearRespondedPulse]);

  useEffect(() => {
    return () => {
      if (respondedTimerRef.current !== null) {
        window.clearTimeout(respondedTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy, activeId]);

  const persistSession = useCallback((sessionId: string, updater: (s: ChatSession) => ChatSession) => {
    setSessions((prev) => prev.map((s) => (s.id === sessionId ? updater(s) : s)));
  }, []);

  const handleNewChat = useCallback(() => {
    const s = newSession();
    setSessions((prev) => [s, ...prev]);
    setActiveId(s.id);
  }, []);

  const handleSelectChat = useCallback((id: string) => {
    setActiveId(id);
  }, []);

  const handleClearChat = useCallback(() => {
    if (!activeId) return;
    persistSession(activeId, (s) => ({
      ...s,
      messages: [],
      updatedAt: Date.now(),
    }));
  }, [activeId, persistSession]);

  const handleDeleteChat = useCallback(
    (id: string) => {
      setSessions((prev) => {
        const next = prev.filter((s) => s.id !== id);
        const sessionsNext = next.length > 0 ? next : [newSession()];
        if (activeId === id) {
          setActiveId(sessionsNext[0].id);
        }
        return sessionsNext;
      });
    },
    [activeId]
  );

  const sendQuery = useCallback(
    async (query: string) => {
      const q = query.trim();
      if (!q || busy) return;

      let sessionId = activeId;
      if (!sessionId) {
        const s = newSession(q);
        setSessions((prev) => [s, ...prev]);
        setActiveId(s.id);
        sessionId = s.id;
      }

      const now = Date.now();
      const userMsg: ChatMessage = { id: msgId(), role: "user", content: q, createdAt: now };

      persistSession(sessionId, (s) => {
        const isFirst = s.messages.length === 0;
        return {
          ...s,
          title: isFirst ? titleFromQuery(q) : s.title,
          updatedAt: now,
          messages: [...s.messages, toStored(userMsg)],
        };
      });

      clearRespondedPulse();
      setBusy(true);
      try {
        const result = await postChat(q, { timeoutMs: timeoutSec * 1000 });
        const assistantMsg: ChatMessage = {
          id: msgId(),
          role: "assistant",
          content: result.answer,
          traceId: result.trace_id,
          createdAt: Date.now(),
        };
        persistSession(sessionId!, (s) => ({
          ...s,
          updatedAt: Date.now(),
          messages: [...s.messages, toStored(assistantMsg)],
        }));
        respondedTimerRef.current = window.setTimeout(() => {
          setRespondedPulse(false);
          respondedTimerRef.current = null;
        }, LLM_ACTIVE_ECHO_MS);
        setRespondedPulse(true);
      } catch (e) {
        const msg =
          e instanceof ApiError
            ? `**Network problem:** ${e.message}\n\nPlease check that the backend is running and try again.`
            : "**Network problem:** Request timed out or failed. Please retry.";
        persistSession(sessionId!, (s) => ({
          ...s,
          updatedAt: Date.now(),
          messages: [
            ...s.messages,
            toStored({ id: msgId(), role: "assistant", content: msg, error: true, createdAt: Date.now() }),
          ],
        }));
      } finally {
        setBusy(false);
      }
    },
    [activeId, busy, clearRespondedPulse, persistSession, timeoutSec]
  );

  const showWelcome = messages.length === 0 && !busy;

  const llmStatus =
    loadError || apiUp === false
      ? ("offline" as const)
      : apiUp === null
        ? ("connecting" as const)
        : busy
          ? ("calling" as const)
          : respondedPulse
            ? ("active" as const)
            : ("ready" as const);

  if (!hydrated) {
    return (
      <div className="flex h-dvh items-center justify-center bg-app-bg text-app-muted">
        Loading…
      </div>
    );
  }

  return (
    <div className="flex h-dvh overflow-hidden bg-app-bg text-app-text">
      <Sidebar
        className="hidden lg:flex"
        sessions={sessions}
        activeId={activeId}
        onNewChat={handleNewChat}
        onSelect={handleSelectChat}
        onDelete={handleDeleteChat}
      />

      <MobileDrawer
        open={drawerOpen}
        sessions={sessions}
        activeId={activeId}
        onClose={() => setDrawerOpen(false)}
        onNewChat={handleNewChat}
        onSelect={handleSelectChat}
        onDelete={handleDeleteChat}
      />

      <div className="flex min-h-0 min-w-0 flex-1 flex-col bg-app-main">
        <ChatHeader
          title={CHAT_HEADER_TITLE}
          llmStatus={llmStatus}
          onRetryConnection={connectApi}
          showMenu
          onMenuClick={() => setDrawerOpen(true)}
          onClear={handleClearChat}
        />

        <ChatBody
          loadError={loadError}
          apiUp={apiUp}
          showWelcome={showWelcome}
          boot={boot}
          messages={messages}
          busy={busy}
          bottomRef={bottomRef}
          sendQuery={sendQuery}
          onRetryApi={connectApi}
          sampleQuestions={boot?.sample_questions ?? []}
          welcomeMessage={boot?.welcome_message}
          inputPlaceholder={boot?.input_placeholder}
          ephemeralHint={boot?.ephemeral_hint}
        />
      </div>
    </div>
  );
}

function ChatBody({
  loadError,
  apiUp,
  showWelcome,
  boot,
  messages,
  busy,
  bottomRef,
  sendQuery,
  onRetryApi,
  sampleQuestions,
  welcomeMessage,
  inputPlaceholder,
  ephemeralHint,
}: {
  loadError: string | null;
  apiUp: boolean | null;
  showWelcome: boolean;
  boot: BootstrapResponse | null;
  messages: ChatMessage[];
  busy: boolean;
  bottomRef: React.RefObject<HTMLDivElement>;
  sendQuery: (q: string) => void;
  onRetryApi: () => void;
  sampleQuestions: BootstrapResponse["sample_questions"];
  welcomeMessage?: string;
  inputPlaceholder?: string;
  ephemeralHint?: string;
}) {
  const apiReady = apiUp === true;
  const samplesDisabled = busy || !apiReady;

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-6 sm:px-8">
        {loadError ? <ErrorBanner loadError={loadError} onRetry={onRetryApi} /> : null}
        {apiUp === null && !loadError ? (
          <p className="mb-4 text-sm text-app-muted">Connecting to API…</p>
        ) : null}

        {showWelcome ? (
          <section className="mx-auto max-w-3xl space-y-4">
            <h3 className="text-lg font-semibold text-app-text">How can I help you today?</h3>
            {welcomeMessage ? (
              <p className="text-sm leading-relaxed text-app-muted">{welcomeMessage}</p>
            ) : null}
            <InfoNotice />
            {sampleQuestions.length > 0 ? (
              <div>
                <p className="mb-2 text-sm text-app-muted">Try a sample question:</p>
                <QuickPrompts
                  questions={sampleQuestions}
                  disabled={samplesDisabled}
                  onSelect={sendQuery}
                />
              </div>
            ) : null}
            {!boot && apiUp ? <LoadingSkeleton /> : null}
          </section>
        ) : null}

        {messages.length > 0 && (
          <section className="mx-auto flex max-w-3xl flex-col gap-6" aria-label="Chat transcript">
            {messages.map((m) => (
              <MessageBubble key={m.id} message={m} />
            ))}
          </section>
        )}

        {busy && (
          <div className="mx-auto mt-4 max-w-3xl" aria-busy="true" aria-label="Assistant is thinking">
            <LoadingSkeleton />
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <InputFooter
        sendQuery={sendQuery}
        busy={busy}
        apiReady={apiReady}
        inputPlaceholder={inputPlaceholder}
        ephemeralHint={ephemeralHint}
      />
    </div>
  );
}

function ErrorBanner({ loadError, onRetry }: { loadError: string; onRetry: () => void }) {
  return (
    <div className="mb-4 rounded-lg border border-red-500/40 bg-red-950/30 px-4 py-3 text-sm text-red-200" role="alert">
      <p>{loadError}</p>
      <pre className="mt-2 overflow-x-auto rounded bg-red-950/50 p-2 text-xs text-red-100/80">
        {`1. Backend: .\\scripts\\run_backend.ps1   (must restart after CORS changes)\n2. Frontend: .\\scripts\\run_frontend.ps1  -> http://localhost:3001`}
      </pre>
      <button
        type="button"
        onClick={onRetry}
        className="mt-3 rounded-lg bg-groww/20 px-3 py-1.5 text-sm font-medium text-groww hover:bg-groww/30"
      >
        Retry connection
      </button>
    </div>
  );
}

function InputFooter({
  sendQuery,
  busy,
  apiReady,
  inputPlaceholder,
  ephemeralHint,
}: {
  sendQuery: (q: string) => void;
  busy: boolean;
  apiReady: boolean;
  inputPlaceholder?: string;
  ephemeralHint?: string;
}) {
  return (
    <footer className="shrink-0 border-t border-app-border bg-app-main/95 px-4 pb-2 pt-1.5 backdrop-blur sm:px-8">
      <div className="mx-auto max-w-3xl">
        <ChatInput
          busy={busy}
          apiReady={apiReady}
          placeholder={inputPlaceholder}
          onSubmit={sendQuery}
        />
      </div>
      <div className="footer-hint mx-auto mt-1.5 max-w-3xl space-y-0.5 text-center text-xs leading-snug">
        <p>
          <span className="text-amber-400/90">Facts-only. No investment advice.</span>
        </p>
        {ephemeralHint ? <p className="text-app-muted">{ephemeralHint}</p> : null}
        <p className="text-amber-400/90">{MARKET_DISCLAIMER}</p>
      </div>
    </footer>
  );
}
