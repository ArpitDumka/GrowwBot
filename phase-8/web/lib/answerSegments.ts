/** Escape HTML entities in plain text segments. */
export function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

export type AnswerSegment =
  | { type: "text"; value: string }
  | { type: "link"; label: string; href: string };

/** Parse markdown links [label](url) and bare https URLs. */
export function parseAnswerSegments(raw: string): AnswerSegment[] {
  const segments: AnswerSegment[] = [];
  const re = /\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)|(https?:\/\/[^\s<>"']+)/g;
  let last = 0;
  let m: RegExpExecArray | null;
  while ((m = re.exec(raw)) !== null) {
    if (m.index > last) {
      segments.push({ type: "text", value: raw.slice(last, m.index) });
    }
    if (m[1] && m[2]) {
      segments.push({ type: "link", label: m[1], href: m[2] });
    } else if (m[3]) {
      segments.push({ type: "link", label: m[3], href: m[3] });
    }
    last = m.index + m[0].length;
  }
  if (last < raw.length) {
    segments.push({ type: "text", value: raw.slice(last) });
  }
  return segments;
}
