"use client";

import type { SampleQuestion } from "@/lib/types";

type Props = {
  questions: SampleQuestion[];
  disabled: boolean;
  onSelect: (text: string) => void;
};

export function SampleQuestions({ questions, disabled, onSelect }: Props) {
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
