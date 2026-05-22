/** Client-side PII warning (Phase 8.3 — do not send PAN/Aadhaar/phone/email). */

const PAN_RE = /\b[A-Z]{5}[0-9]{4}[A-Z]\b/i;
const AADHAAR_RE = /\b\d{4}\s?\d{4}\s?\d{4}\b/;
const EMAIL_RE = /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/i;
const PHONE_RE = /\b(?:\+91[\s-]?)?[6-9]\d{9}\b/;

export function detectPii(text: string): string | null {
  const t = text.trim();
  if (!t) return null;
  if (PAN_RE.test(t)) return "PAN number";
  if (AADHAAR_RE.test(t)) return "Aadhaar number";
  if (EMAIL_RE.test(t)) return "email address";
  if (PHONE_RE.test(t)) return "phone number";
  return null;
}
