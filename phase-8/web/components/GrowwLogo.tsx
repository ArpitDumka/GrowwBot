"use client";

import Image from "next/image";

/**
 * Groww brand mark — PNG served from `/groww-logo.png` (place asset in `public/`).
 */
export function GrowwLogo({ className = "h-9 w-9" }: { className?: string }) {
  return (
    <Image
      src="/groww-logo.png"
      alt="Groww"
      width={128}
      height={128}
      className={`shrink-0 object-contain ${className}`}
      priority
    />
  );
}
