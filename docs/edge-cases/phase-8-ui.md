# Phase 8 — Edge Cases: UI / UX

> Companion to `../architecture.md` Phase 8. Next.js on Vercel. Always-visible "Facts-only" disclaimer.

## Edge cases

| # | ID | Trigger | Expected behavior | Detection | Mitigation | Priority |
|---|---|---|---|---|---|---|
| 1 | 8.01 | User scrolls and **disclaimer leaves the viewport** | Disclaimer is `position: sticky` at the top — never scrolls away | Visual regression test | CSS sticky positioning | P0 |
| 2 | 8.02 | **Citation link is broken** at click time (Groww rotated the URL) | Link still opens (we don't pre-validate at click); a separate background job (Phase 10) re-checks all 10 URLs nightly and alerts on 404 | Nightly link-check job | Alert + dashboard | P0 |
| 3 | 8.03 | Long answer + long URL **wraps badly on mobile** | CSS `overflow-wrap: anywhere` on the answer container; URL truncated visually but full URL retained in `href` | Manual + screenshot test at 360px width | Word-break CSS | P1 |
| 4 | 8.04 | A **sample question** has a typo or refers to a scheme not in corpus | Sample questions are derived from a `config/sample_questions.yaml` that is validated at build time against `sources.yaml` | Build-time validator | YAML cross-check | P0 |
| 5 | 8.05 | User pastes **PII** in the input box | Client-side detector strips obvious PII patterns before submit; server-side guard (Phase 5) is the source of truth | JS regex on input change | Two-layer scrub: warn user + server-side enforce | P0 |
| 6 | 8.06 | **Session is lost on refresh** (no transcript persistence) | Acceptable for v1: chat is ephemeral. Show a brief "history is not saved" hint in footer. | None | Documented behavior; v2 adds local-storage persistence (no PII!) | P1 |
| 7 | 8.07 | User submits **rapid repeated** clicks of "Send" | Submit button is disabled while a request is in flight; second click is no-op | Disabled state | Button state machine | P0 |
| 8 | 8.08 | **Network error** mid-request — UI hangs | Request has a 10s client-side timeout; on failure, show "Network problem, please retry" with a retry button | `AbortController` + timeout | Always-recoverable error state | P0 |
| 9 | 8.09 | **RTL or right-to-left text** input rendering | Detect direction; the answer renders LTR (we only support English answers); input field auto-detects direction for display | `dir="auto"` on input | Native browser support | P2 |
| 10 | 8.10 | Browser **autofill** triggers on the input field (filling email/name) | Input has `autocomplete="off"` and `name="question"` (not "email" / "name") | Inspect DOM | HTML attributes | P1 |
| 11 | 8.11 | **Citation link** could open the same page on top of the chat | Link uses `target="_blank" rel="noopener noreferrer"` — always opens in a new tab | Code review | Link rendering helper | P0 |
| 12 | 8.12 | A user shares the page URL — we leak their query in the address bar | The chat input is **not** in the URL; we use POST, not GET. URL stays static (`/chat`). | Manual check | API contract | P0 |
| 13 | 8.13 | **Refusal templates** render without their educational link being clickable | Markdown renderer is enabled for refusal text too, with the same allow-list as answers | Test on each refusal template | Same renderer pipeline | P1 |
| 14 | 8.14 | A user views the **page source** to "see the prompt" | System prompts and chunk text are server-side only; client only sees the final answer + citation | Code review | Defense in depth — server-side composer | P0 |
| 15 | 8.15 | Next.js **cold start** delay shows a blank page | Loading skeleton with the disclaimer banner pre-rendered via SSR | Lighthouse / TTI metric | Loading state | P1 |
| 16 | 8.16 | **Accessibility**: screen reader announces the answer **before** the citation | Use `aria-live="polite"` on the answer container; citation is a separate semantically-grouped link | a11y audit | Semantic HTML + ARIA | P1 |
| 17 | 8.17 | High contrast / dark mode renders citation link unreadable | Citation link uses a contrast-AA color in both themes (≥ 4.5:1) | Lighthouse a11y | Theme tokens | P2 |
| 18 | 8.18 | User's input contains **markdown** (e.g., backticks, links) and we render it raw | Input is HTML-escaped before display in transcript | XSS test | Escape on render | P0 |
| 19 | 8.19 | Two browser tabs open with different sessions — race in local storage (v2) | Per-tab session id; no shared mutable storage | Manual test | Tab-scoped state | P2 |
| 20 | 8.20 | Next.js client-side state lost on full page navigation | Keep transcript in `useState` and avoid hard navigations; use App Router transitions | Profiling | React state | P1 |

## Disclaimer wording (locked)

```
Facts-only. No investment advice.
```

This string is the source of truth and must appear:
1. As a sticky banner above the chat,
2. As a footer below the input,
3. In the page `<title>` suffix (e.g., `HDFC MF FAQ — Facts-only`).
