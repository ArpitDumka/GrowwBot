import { IconInfo } from "./Icons";

export function InfoNotice() {
  return (
    <div className="flex items-start gap-3 rounded-xl border border-app-border bg-app-surface/60 px-4 py-3 text-sm text-app-muted">
      <IconInfo className="mt-0.5 shrink-0 text-app-muted" />
      <p>
        Facts from official Groww scheme pages for 10 HDFC funds — no investment advice, predictions,
        or recommendations. Say <strong className="font-medium text-app-text">help</strong> anytime
        for examples.
      </p>
    </div>
  );
}
