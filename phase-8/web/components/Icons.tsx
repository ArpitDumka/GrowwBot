import type { ReactNode } from "react";

type IconProps = { className?: string };

/** Merge size + shrink so color-only className cannot drop width/height. */
function iconCls(size: string, className?: string): string {
  return [size, "shrink-0", className].filter(Boolean).join(" ");
}

function Svg({
  size,
  className,
  children,
  strokeWidth = 1.8,
}: {
  size: string;
  className?: string;
  children: ReactNode;
  strokeWidth?: number;
}) {
  return (
    <svg
      className={iconCls(size, className)}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      aria-hidden
    >
      {children}
    </svg>
  );
}

export function IconPlus({ className }: IconProps) {
  return (
    <Svg size="h-4 w-4" className={className} strokeWidth={2}>
      <path d="M12 5v14M5 12h14" strokeLinecap="round" />
    </Svg>
  );
}

export function IconX({ className }: IconProps) {
  return (
    <Svg size="h-5 w-5" className={className} strokeWidth={2}>
      <path d="M6 6l12 12M18 6L6 18" strokeLinecap="round" />
    </Svg>
  );
}

export function IconMenu({ className }: IconProps) {
  return (
    <Svg size="h-5 w-5" className={className} strokeWidth={2}>
      <path d="M4 7h16M4 12h16M4 17h16" strokeLinecap="round" />
    </Svg>
  );
}

export function IconChart({ className }: IconProps) {
  return (
    <Svg size="h-4 w-4" className={className}>
      <path d="M4 19V5M10 19V9M16 19v-6M22 19H2" strokeLinecap="round" />
    </Svg>
  );
}

export function IconTrend({ className }: IconProps) {
  return (
    <Svg size="h-4 w-4" className={className}>
      <path d="M4 18l6-6 4 4 6-8" strokeLinecap="round" strokeLinejoin="round" />
    </Svg>
  );
}

export function IconChat({ className }: IconProps) {
  return (
    <Svg size="h-4 w-4" className={className}>
      <path
        d="M6 8.5A4.5 4.5 0 0110.5 4h3A4.5 4.5 0 0118 8.5V12a4.5 4.5 0 01-4.5 4.5h-2.2L8 20v-3.5H10.5A4.5 4.5 0 016 12V8.5z"
        strokeLinejoin="round"
      />
    </Svg>
  );
}

export function IconHistory({ className }: IconProps) {
  return (
    <Svg size="h-4 w-4" className={className}>
      <path d="M4 6h16M4 12h10M4 18h6" strokeLinecap="round" />
      <path d="M16 14l3 3-3 3" strokeLinecap="round" strokeLinejoin="round" />
    </Svg>
  );
}

export function IconBot({ className }: IconProps) {
  return (
    <Svg size="h-4 w-4" className={className}>
      <rect x="5" y="8" width="14" height="10" rx="3" />
      <circle cx="9.5" cy="13" r="1" fill="currentColor" stroke="none" />
      <circle cx="14.5" cy="13" r="1" fill="currentColor" stroke="none" />
      <path d="M9 8V6a3 3 0 016 0v2" strokeLinecap="round" />
    </Svg>
  );
}

export function IconPaperclip({ className }: IconProps) {
  return (
    <Svg size="h-5 w-5" className={className}>
      <path
        d="M8.5 12.5l6.2-6.2a3 3 0 114.2 4.2l-7.4 7.4a4.5 4.5 0 01-6.4-6.4l8-8"
        strokeLinecap="round"
      />
    </Svg>
  );
}

export function IconSend({ className }: IconProps) {
  return (
    <Svg size="h-4 w-4" className={className} strokeWidth={2}>
      <path d="M5 12h14M14 7l5 5-5 5" strokeLinecap="round" strokeLinejoin="round" />
    </Svg>
  );
}

export function IconThumbsUp({ className }: IconProps) {
  return (
    <Svg size="h-4 w-4" className={className} strokeWidth={1.6}>
      <path
        d="M7 11v8M7 11l-2-2V8a2 2 0 012-2h2l3-6 1 6h6a2 2 0 012 2v5a2 2 0 01-2 2H7z"
        strokeLinejoin="round"
      />
    </Svg>
  );
}

export function IconThumbsDown({ className }: IconProps) {
  return (
    <Svg size="h-4 w-4" className={className} strokeWidth={1.6}>
      <path
        d="M17 13v-8M17 13l2 2v1a2 2 0 01-2 2h-2l-3 6-1-6H7a2 2 0 01-2-2v-5a2 2 0 012-2h10z"
        strokeLinejoin="round"
      />
    </Svg>
  );
}

export function IconLink({ className }: IconProps) {
  return (
    <Svg size="h-3.5 w-3.5" className={className} strokeWidth={2}>
      <path d="M10 14a4 4 0 005.7 0l2.3-2.3a4 4 0 00-5.7-5.7L12 7" strokeLinecap="round" />
      <path d="M14 10a4 4 0 00-5.7 0L6 12.3a4 4 0 005.7 5.7L12 17" strokeLinecap="round" />
    </Svg>
  );
}

export function IconBuilding({ className }: IconProps) {
  return (
    <Svg size="h-5 w-5" className={className}>
      <path d="M5 20V6l7-3 7 3v14" strokeLinejoin="round" />
      <path d="M9 10h2M9 14h2M13 10h2M13 14h2" strokeLinecap="round" />
    </Svg>
  );
}

export function IconTrash({ className }: IconProps) {
  return (
    <Svg size="h-3.5 w-3.5" className={className}>
      <path
        d="M4 7h16M9 7V5a1 1 0 011-1h4a1 1 0 011 1v2M10 11v6M14 11v6M6 7l1 12a1 1 0 001 1h8a1 1 0 001-1l1-12"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </Svg>
  );
}

export function IconWarning({ className }: IconProps) {
  return (
    <Svg size="h-4 w-4" className={className} strokeWidth={2}>
      <path d="M12 4l9 16H3L12 4z" strokeLinejoin="round" />
      <path d="M12 10v4M12 17h.01" strokeLinecap="round" />
    </Svg>
  );
}

export function IconInfo({ className }: IconProps) {
  return (
    <Svg size="h-4 w-4" className={className} strokeWidth={2}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v5M12 8h.01" strokeLinecap="round" />
    </Svg>
  );
}
