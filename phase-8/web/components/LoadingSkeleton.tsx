export function LoadingSkeleton() {
  return (
    <div
      className="animate-pulse space-y-3 rounded-xl border border-app-border bg-app-surface p-4"
      aria-hidden
    >
      <div className="h-3 w-3/4 rounded bg-app-border/80" />
      <div className="h-3 w-full rounded bg-app-border/80" />
      <div className="h-3 w-5/6 rounded bg-app-border/80" />
    </div>
  );
}
