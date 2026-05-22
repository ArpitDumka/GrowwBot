"use client";

import type { ChatSession } from "@/lib/types";
import { GrowwLogo } from "./GrowwLogo";
import { IconChart, IconPlus, IconTrend } from "./Icons";
import { SessionListItem } from "./SessionListItem";

type Props = {
  sessions: ChatSession[];
  activeId: string | null;
  onNewChat: () => void;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  className?: string;
};

const INSIGHT_LINKS = [
  { id: "insight-market", label: "Market Insights", icon: IconTrend },
  { id: "insight-portfolio", label: "Portfolio Analysis", icon: IconChart },
] as const;

export function Sidebar({ sessions, activeId, onNewChat, onSelect, onDelete, className = "" }: Props) {
  return (
    <aside
      className={`flex h-full w-[280px] shrink-0 flex-col border-r border-app-border bg-app-sidebar ${className}`}
    >
      <BrandHeader />

      <div className="px-4 pb-4">
        <button
          type="button"
          onClick={onNewChat}
          className="flex w-full items-center justify-center gap-2 rounded-full bg-groww py-3 text-sm font-semibold text-app-bg transition hover:bg-groww-bright"
        >
          <IconPlus className="h-4 w-4" />
          New Chat
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto px-3">
        <p className="px-2 pb-2 text-[10px] font-semibold tracking-widest text-app-muted">RECENT CHATS</p>
        <ul className="space-y-1">
          {sessions.length === 0 && (
            <li className="px-3 py-2 text-sm text-app-muted">No chats yet — start one above.</li>
          )}
          {sessions.map((s) => (
            <SessionListItem
              key={s.id}
              session={s}
              active={s.id === activeId}
              onSelect={() => onSelect(s.id)}
              onDelete={() => onDelete(s.id)}
            />
          ))}
        </ul>

        <p className="mt-6 px-2 pb-2 text-[10px] font-semibold tracking-widest text-app-muted">INSIGHTS</p>
        <ul className="space-y-1">
          {INSIGHT_LINKS.map(({ id, label, icon: Icon }) => (
            <li key={id}>
              <button
                type="button"
                onClick={onNewChat}
                className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm text-app-muted transition hover:bg-app-surface/60 hover:text-app-text"
              >
                <Icon className="h-4 w-4 shrink-0" />
                <span>{label}</span>
              </button>
            </li>
          ))}
        </ul>
      </nav>

    </aside>
  );
}

function BrandHeader() {
  return (
    <div className="flex items-center gap-3 px-5 py-6">
      <GrowwLogo className="h-10 w-10" />
      <div>
        <h1 className="text-lg font-bold leading-tight text-app-text">HDFC MF FAQ</h1>
        <p className="text-xs text-app-muted">Institutional Grade AI</p>
      </div>
    </div>
  );
}