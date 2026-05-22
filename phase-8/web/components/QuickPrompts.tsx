"use client";

import type { SampleQuestion } from "@/lib/types";

type Props = {
  questions: SampleQuestion[];
  disabled: boolean;
  onSelect: (text: string) => void;
  compact?: boolean;
};

/** Chip or card layout for sample / quick questions. */
export function QuickPrompts({ questions, disabled, onSelect, compact }: Props) {
  if (questions.length === 0) return null;

  if (compact) {
    return (
      <div className="flex flex-wrap gap-2" aria-label="Quick questions">
        {questions.map((q) => (
          <button
            key={q.id}
            type="button"
            disabled={disabled}
            onClick={() => onSelect(q.text)}
            title={q.text}
            className="max-w-[min(100%,280px)] truncate rounded-full border border-app-border bg-app-surface/80 px-3 py-1.5 text-xs text-app-text transition hover:border-groww/50 hover:bg-groww/10 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {q.text}
          </button>
        ))}
      </div>
    );
  }

  return (
    <ul className="grid gap-2" aria-label="Sample questions">
      {questions.map((q) => (
        <li key={q.id}>
          <button
            type="button"
            disabled={disabled}
            onClick={() => onSelect(q.text)}
            className="w-full rounded-xl border border-app-border bg-app-surface px-4 py-3 text-left text-sm leading-snug text-app-text transition hover:border-groww/40 hover:bg-groww/10 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {q.text}
          </button>
        </li>
      ))}
    </ul>
  );
}
