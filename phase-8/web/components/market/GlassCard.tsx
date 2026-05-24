"use client";

import type { ReactNode } from "react";

type Props = {
  children: ReactNode;
  className?: string;
};

export function GlassCard({ children, className = "" }: Props) {
  return (
    <div
      className={`rounded-2xl border border-white/10 bg-gradient-to-br from-white/[0.08] to-white/[0.02] p-5 shadow-lg shadow-black/20 backdrop-blur-md transition duration-300 hover:-translate-y-0.5 hover:border-groww/25 hover:shadow-groww/10 ${className}`}
    >
      {children}
    </div>
  );
}
