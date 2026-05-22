"use client";

import { type FormEvent, type Ref, useEffect, useRef, useState } from "react";
import { detectPii } from "@/lib/pii";
import { IconPaperclip, IconSend } from "./Icons";

type Props = {
  /** Blocks typing (e.g. while assistant is replying). */
  busy: boolean;
  /** When false, user can type but Send stays off until API is reachable. */
  apiReady: boolean;
  placeholder?: string;
  onSubmit: (query: string) => void;
};

export function ChatInput({
  busy,
  apiReady,
  placeholder = "Ask about an HDFC fund — expense ratio, exit load, minimum SIP…",
  onSubmit,
}: Props) {
  const [value, setValue] = useState("");
  const [piiWarning, setPiiWarning] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const wasBusyRef = useRef(false);

  const canSend = !busy && apiReady && value.trim().length > 0 && !piiWarning;

  function focusInput() {
    const el = inputRef.current;
    if (!el || el.disabled) return;
    el.focus({ preventScroll: true });
  }

  useEffect(() => {
    if (wasBusyRef.current && !busy && apiReady) {
      const id = window.requestAnimationFrame(() => focusInput());
      return () => window.cancelAnimationFrame(id);
    }
    wasBusyRef.current = busy;
  }, [busy, apiReady]);

  useEffect(() => {
    if (apiReady && !busy) focusInput();
  }, [apiReady]);

  function handleChange(next: string) {
    setValue(next);
    const kind = detectPii(next);
    setPiiWarning(kind ? `Remove ${kind} before sending — we cannot process personal data.` : null);
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const q = value.trim();
    if (!q || !canSend) return;
    onSubmit(q);
    setValue("");
    setPiiWarning(null);
  }

  return (
    <form onSubmit={handleSubmit} className="w-full">
      {piiWarning && (
        <p className="mb-2 text-sm text-amber-400" role="alert">
          {piiWarning}
        </p>
      )}
      {!apiReady && !busy && (
        <p className="mb-2 text-xs text-amber-400/90">
          Connect to the API to send — you can still type your question below.
        </p>
      )}
      <InputRow
        inputRef={inputRef}
        value={value}
        busy={busy}
        canSend={canSend}
        placeholder={placeholder}
        onChange={handleChange}
      />
    </form>
  );
}

function InputRow({
  inputRef,
  value,
  busy,
  canSend,
  placeholder,
  onChange,
}: {
  inputRef: Ref<HTMLInputElement>;
  value: string;
  busy: boolean;
  canSend: boolean;
  placeholder: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="flex items-end gap-2 rounded-2xl border border-app-border bg-app-surface px-3 py-2 focus-within:border-groww/50">
      <input
        ref={inputRef}
        type="text"
        name="question"
        autoComplete="off"
        dir="auto"
        value={value}
        disabled={busy}
        maxLength={500}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="min-h-[44px] flex-1 bg-transparent py-2 text-[15px] text-app-text outline-none placeholder:text-app-muted disabled:cursor-not-allowed disabled:opacity-60"
        aria-label="Your question"
      />
      <button
        type="button"
        disabled={busy}
        className="rounded-lg p-2 text-app-muted hover:text-app-text disabled:opacity-40"
        aria-label="Attach file"
        tabIndex={-1}
      >
        <IconPaperclip />
      </button>
      <button
        type="submit"
        disabled={!canSend}
        className="mb-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-groww text-app-bg transition hover:bg-groww-bright disabled:cursor-not-allowed disabled:opacity-50"
        aria-label="Send question"
      >
        <IconSend />
      </button>
    </div>
  );
}
