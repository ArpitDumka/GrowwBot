"use client";

type Props = {
  replies: string[];
  disabled: boolean;
  onSelect: (text: string) => void;
};

/** Quick-reply chips after contextual assistant messages (yes / no / samples). */
export function ReplyChips({ replies, disabled, onSelect }: Props) {
  if (replies.length === 0) return null;

  return (
    <div
      className="mx-auto flex max-w-3xl flex-wrap gap-2 border-t border-app-border/60 px-4 py-3 sm:px-8"
      aria-label="Suggested replies"
    >
      {replies.map((text) => (
        <button
          key={text}
          type="button"
          disabled={disabled}
          onClick={() => onSelect(text)}
          className="rounded-full border border-groww/40 bg-groww/10 px-4 py-2 text-sm font-medium text-groww transition hover:bg-groww/20 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {text}
        </button>
      ))}
    </div>
  );
}
