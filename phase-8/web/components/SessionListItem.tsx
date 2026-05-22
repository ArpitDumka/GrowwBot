"use client";

import type { ChatSession } from "@/lib/types";
import { IconChart, IconChat, IconTrash, IconTrend } from "./Icons";

type Props = {
  session: ChatSession;
  active: boolean;
  onSelect: () => void;
  onDelete: () => void;
};

export function SessionListItem({ session, active, onSelect, onDelete }: Props) {
  const Icon = iconForTitle(session.title);

  return (
    <li className="group relative">
      <button
        type="button"
        onClick={onSelect}
        className={`flex w-full items-center gap-3 rounded-lg py-2.5 pl-3 pr-9 text-left text-sm transition ${
          active
            ? "border border-groww/40 bg-app-surface text-groww"
            : "text-app-muted hover:bg-app-surface/60 hover:text-app-text"
        }`}
      >
        <Icon className={`h-4 w-4 shrink-0 ${active ? "text-groww" : ""}`} />
        <span className="truncate">{session.title}</span>
      </button>
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          onDelete();
        }}
        className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-1.5 text-app-muted opacity-70 transition hover:bg-red-500/15 hover:text-red-400 sm:opacity-0 sm:group-hover:opacity-100 focus:opacity-100"
        aria-label={`Delete chat ${session.title}`}
        title="Delete chat"
      >
        <IconTrash className="h-3.5 w-3.5" />
      </button>
    </li>
  );
}

function iconForTitle(title: string) {
  const t = title.toLowerCase();
  if (t.includes("market")) return IconTrend;
  if (t.includes("portfolio")) return IconChart;
  if (title === "New Chat") return IconChat;
  return IconChart;
}
