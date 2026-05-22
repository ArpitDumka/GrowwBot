"use client";

import { useState } from "react";
import { extractSourceUrl, stripSourceLine } from "@/lib/extractSource";
import { AnswerBody } from "@/lib/parseAnswer";
import type { ChatMessage } from "@/lib/types";
import { GrowwLogo } from "./GrowwLogo";
import { IconBot, IconLink, IconThumbsDown, IconThumbsUp } from "./Icons";

function formatTime(ts?: number): string {
  if (!ts) return "";
  return new Date(ts).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

export function MessageBubble({ message }: { message: ChatMessage }) {
  if (message.role === "user") {
    return <UserMessage message={message} />;
  }
  return <AssistantMessage message={message} />;
}

function UserMessage({ message }: { message: ChatMessage }) {
  return (
    <div className="flex flex-col items-end" data-role="user">
      <UserMessageBubble content={message.content} />
      {message.createdAt ? (
        <p className="mt-1 text-[11px] text-app-muted">{formatTime(message.createdAt)}</p>
      ) : null}
    </div>
  );
}

function UserMessageBubble({ content }: { content: string }) {
  return (
    <div className="max-w-[min(100%,520px)] rounded-2xl bg-groww px-4 py-3 text-app-bg">
      <p className="whitespace-pre-wrap break-words text-[15px] leading-relaxed">{content}</p>
    </div>
  );
}

function AssistantMessage({ message }: { message: ChatMessage }) {
  const [feedback, setFeedback] = useState<"up" | "down" | null>(null);
  const sourceUrl = extractSourceUrl(message.content);
  const bodyText = stripSourceLine(message.content);

  return (
    <div className="flex justify-start" data-role="assistant">
      <div className="max-w-[min(100%,640px)]">
        <div className="mb-2 flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-groww/20 text-groww">
            <IconBot className="h-4 w-4" />
          </span>
          <span className="text-sm font-medium text-groww">Assistant</span>
        </div>

        <div
          className={`rounded-xl border px-4 py-4 ${
            message.error
              ? "border-red-500/40 bg-red-950/30 text-red-200"
              : "border-app-border bg-app-surface text-app-text"
          }`}
        >
          <div className="bot-answer" style={{ overflowWrap: "anywhere" }}>
            <AnswerBody text={bodyText} />
          </div>

          {sourceUrl && !message.error ? (
            <a
              href={sourceUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-4 inline-flex items-center gap-2 rounded-full border border-app-border bg-app-bg/60 px-3 py-1.5 text-xs font-medium text-app-text transition hover:border-groww/50 hover:text-groww"
            >
              <GrowwLogo className="h-4 w-4" />
              Groww source
              <IconLink className="text-groww" />
            </a>
          ) : null}

          <div className="mt-3 flex items-center justify-between gap-2 border-t border-app-border pt-3">
            {message.traceId ? (
              <p className="truncate text-[11px] text-app-muted" aria-label="Trace identifier">
                trace_id: {message.traceId.slice(0, 12)}
              </p>
            ) : (
              <span />
            )}
            <FeedbackButtons feedback={feedback} setFeedback={setFeedback} />
          </div>
        </div>
      </div>
    </div>
  );
}

function FeedbackButtons({
  feedback,
  setFeedback,
}: {
  feedback: "up" | "down" | null;
  setFeedback: (v: "up" | "down" | null) => void;
}) {
  return (
    <div className="flex shrink-0 gap-1">
      <button
        type="button"
        onClick={() => setFeedback(feedback === "up" ? null : "up")}
        className={`rounded p-1.5 ${feedback === "up" ? "text-groww" : "text-app-muted hover:text-app-text"}`}
        aria-label="Helpful"
      >
        <IconThumbsUp />
      </button>
      <button
        type="button"
        onClick={() => setFeedback(feedback === "down" ? null : "down")}
        className={`rounded p-1.5 ${feedback === "down" ? "text-red-400" : "text-app-muted hover:text-app-text"}`}
        aria-label="Not helpful"
      >
        <IconThumbsDown />
      </button>
    </div>
  );
}
