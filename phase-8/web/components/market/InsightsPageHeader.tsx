"use client";

import { GrowwLogo } from "../GrowwLogo";
import { IconMenu } from "../Icons";

type Props = {
  title: string;
  subtitle?: string;
  onBack: () => void;
  onMenuClick?: () => void;
  showMenu?: boolean;
};

export function InsightsPageHeader({ title, subtitle, onBack, onMenuClick, showMenu }: Props) {
  return (
    <header className="flex shrink-0 items-center justify-between border-b border-app-border bg-app-main/80 px-4 py-4 backdrop-blur sm:px-6">
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
        <div>
          <h2 className="text-lg font-semibold text-groww sm:text-xl">{title}</h2>
          {subtitle ? <p className="text-xs text-app-muted">{subtitle}</p> : null}
        </div>
      </div>
      <button
        type="button"
        onClick={onBack}
        className="rounded-lg border border-app-border bg-app-surface px-3 py-1.5 text-sm text-app-text transition hover:border-groww/40 hover:text-groww"
      >
        ← Back to Chat
      </button>
    </header>
  );
}
