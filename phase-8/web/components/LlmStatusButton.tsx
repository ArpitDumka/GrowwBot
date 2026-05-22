"use client";

export type LlmRuntimeStatus = "connecting" | "offline" | "ready" | "calling" | "active";

type Props = {
  status: LlmRuntimeStatus;
  /** When API is unreachable or still connecting, click retries health/bootstrap. */
  onRetryConnection?: () => void;
};

export function LlmStatusButton({ status, onRetryConnection }: Props) {
  const { dotClass, label, subLabel, pulse } = meta(status);
  const interactive = status === "offline" || status === "connecting";
  const retry = onRetryConnection ?? (() => {});

  const inner = (
    <>
      <span
        className={`h-2 w-2 shrink-0 rounded-full ${dotClass} ${pulse ? "animate-pulse" : ""}`}
        aria-hidden
      />
      <span className="flex flex-col items-start leading-none">
        <span className="text-[11px] font-medium sm:text-xs">{label}</span>
        {subLabel ? (
          <span className="mt-0.5 max-w-[7rem] truncate text-[9px] font-normal text-app-muted sm:max-w-[9rem] sm:text-[10px]">
            {subLabel}
          </span>
        ) : null}
      </span>
    </>
  );

  const shellClass =
    "inline-flex max-w-[10rem] items-center gap-2 rounded-full border border-app-border bg-app-surface px-2.5 py-1 text-left text-app-text transition sm:max-w-none sm:px-3 sm:py-1.5";

  if (interactive) {
    return (
      <button
        type="button"
        onClick={() => retry()}
        className={`${shellClass} hover:border-groww/40 hover:bg-app-main/80`}
        aria-label={`${label}. Click to retry connection.`}
      >
        {inner}
      </button>
    );
  }

  return (
    <span
      role="status"
      aria-live="polite"
      aria-busy={status === "calling"}
      aria-label={subLabel ? `${label}. ${subLabel}` : label}
      className={shellClass}
    >
      {inner}
    </span>
  );
}

function meta(status: LlmRuntimeStatus): {
  dotClass: string;
  label: string;
  subLabel?: string;
  pulse: boolean;
} {
  switch (status) {
    case "connecting":
      return {
        dotClass: "bg-amber-400",
        label: "API",
        subLabel: "Connecting…",
        pulse: true,
      };
    case "offline":
      return {
        dotClass: "bg-red-400",
        label: "Offline",
        subLabel: "Tap to retry",
        pulse: false,
      };
    case "calling":
      return {
        dotClass: "bg-groww",
        label: "LLM",
        subLabel: "Calling…",
        pulse: true,
      };
    case "active":
      return {
        dotClass: "bg-groww-bright",
        label: "LLM",
        subLabel: "Active",
        pulse: true,
      };
    case "ready":
      return {
        dotClass: "bg-emerald-400",
        label: "LLM",
        subLabel: "Standby",
        pulse: false,
      };
  }
}
