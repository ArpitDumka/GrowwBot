"use client";

import type { ChatSession } from "@/lib/types";
import { GrowwLogo } from "./GrowwLogo";
import { IconChart, IconPlus, IconTrend, IconX } from "./Icons";
import { SessionListItem } from "./SessionListItem";

type Props = {
  open: boolean;
  sessions: ChatSession[];
  activeId: string | null;
  onClose: () => void;
  onNewChat: () => void;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
};

export function MobileDrawer({
  open,
  sessions,
  activeId,
  onClose,
  onNewChat,
  onSelect,
  onDelete,
}: Props) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 lg:hidden">
      <button
        type="button"
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        aria-label="Close menu backdrop"
        onClick={onClose}
      />
      <div className="relative flex h-full w-[min(320px,85vw)] flex-col bg-app-sidebar shadow-2xl">
        <div className="flex items-center justify-between px-5 py-5">
          <DrawerHeaderLeft />
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-2 text-app-muted hover:bg-app-surface hover:text-app-text"
            aria-label="Close menu"
          >
            <IconX />
          </button>
        </div>

        <div className="px-4 pb-4">
          <button
            type="button"
            onClick={() => {
              onNewChat();
              onClose();
            }}
            className="flex w-full items-center justify-center gap-2 rounded-full bg-groww py-3 text-sm font-semibold text-app-bg"
          >
            <IconPlus className="h-4 w-4" />
            New Chat
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto px-3">
          <p className="px-2 pb-2 text-[10px] font-semibold tracking-widest text-app-muted">TODAY</p>
          <ul className="space-y-1">
            {sessions.length === 0 && (
              <li className="px-3 py-2 text-sm text-app-muted">No chats yet.</li>
            )}
            {sessions.map((s) => (
              <SessionListItem
                key={s.id}
                session={s}
                active={s.id === activeId}
                onSelect={() => {
                  onSelect(s.id);
                  onClose();
                }}
                onDelete={() => {
                  onDelete(s.id);
                  onClose();
                }}
              />
            ))}
          </ul>

          <p className="mt-6 px-2 pb-2 text-[10px] font-semibold tracking-widest text-app-muted">INSIGHTS</p>
          <ul className="space-y-1">
            <InsightRow label="Market Insights" icon={IconTrend} onNewChat={onNewChat} onClose={onClose} />
            <InsightRow label="Portfolio Analysis" icon={IconChart} onNewChat={onNewChat} onClose={onClose} />
          </ul>
        </nav>
      </div>
    </div>
  );
}

function DrawerHeaderLeft() {
  return (
    <div className="flex items-center gap-3">
      <GrowwLogo className="h-10 w-10" />
      <div>
        <h1 className="text-base font-bold text-app-text">HDFC MF FAQ</h1>
        <p className="text-xs text-app-muted">Institutional Grade AI</p>
      </div>
    </div>
  );
}

function InsightRow({
  label,
  icon: Icon,
  onNewChat,
  onClose,
}: {
  label: string;
  icon: typeof IconTrend;
  onNewChat: () => void;
  onClose: () => void;
}) {
  return (
    <li>
      <button
        type="button"
        onClick={() => {
          onNewChat();
          onClose();
        }}
        className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-app-muted hover:bg-app-surface/50"
      >
        <Icon className="h-4 w-4" />
        {label}
      </button>
    </li>
  );
}
