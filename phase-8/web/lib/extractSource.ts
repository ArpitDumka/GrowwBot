/** Pull Groww citation URL from assistant answer text. */
export function extractSourceUrl(content: string): string | null {
  const m = content.match(/Source:\s*(https?:\/\/[^\s]+)/i);
  return m ? m[1].replace(/[.,;)]+$/, "") : null;
}

/** Remove the Source: line so the pill can show it separately. */
export function stripSourceLine(content: string): string {
  return content.replace(/\n?Source:\s*https?:\/\/[^\s]+\s*/gi, "").trim();
}
