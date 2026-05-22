"use client";

import { GrowwLogo } from "./GrowwLogo";
import { IconHistory, IconMenu } from "./Icons";
import { LlmStatusButton, type LlmRuntimeStatus } from "./LlmStatusButton";

type Props = {
  title: string;
  modelLabel?: string;
  llmStatus: LlmRuntimeStatus;
  onRetryConnection?: () => void;
  onMenuClick?: () => void;
  onClear: () => void;
  showMenu?: boolean;
};

export function ChatHeader({
  title,
  modelLabel = "Llama 3.3",
  llmStatus,
  onRetryConnection,
  onMenuClick,
  onClear,
  showMenu = false,
}: Props) {
  return (
    <header className="flex shrink-0 items-center justify-between border-b border-app-border bg-app-main/80 px-4 py-4 backdrop-blur sm:px-6">
      <TitleRow title={title} showMenu={showMenu} onMenuClick={onMenuClick} />

      <div className="flex flex-wrap items-center justify-end gap-2 sm:gap-3">
        <span className="rounded-full border border-app-border bg-app-surface px-2.5 py-1 text-[11px] text-app-muted sm:px-3 sm:py-1.5 sm:text-xs">
          Model: {modelLabel}
        </span>
        <LlmStatusButton status={llmStatus} onRetryConnection={onRetryConnection} />
        <button
          type="button"
          className="rounded-lg p-2 text-app-muted hover:bg-app-surface hover:text-app-text"
          aria-label="History"
        >
          <IconHistory />
        </button>
        <button
          type="button"
          onClick={onClear}
          className="text-sm text-app-muted transition hover:text-groww"
        >
          Clear Chat
        </button>
      </div>
    </header>
  );
}

function TitleRow({
  title,
  showMenu,
  onMenuClick,
}: {
  title: string;
  showMenu: boolean;
  onMenuClick?: () => void;
}) {
  return (
    <div className="flex items-center gap-3">
      <GrowwLogo className="h-8 w-8 shrink-0 lg:hidden" />
      {showMenu && onMenuClick && (
        <button
          type="button"
          onClick={onMenuClick}
          className="rounded-lg p-2 text-app-muted hover:bg-app-surface lg:hidden"
          aria-label="Open menu"
        >
          <IconMenu />
        </button>
      )}
      <h2 className="truncate text-lg font-semibold text-groww sm:text-xl">{title}</h2>
    </div>
  );
}
