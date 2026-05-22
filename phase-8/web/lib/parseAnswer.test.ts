import { describe, expect, it } from "vitest";
import { escapeHtml, parseAnswerSegments } from "./answerSegments";

describe("parseAnswerSegments", () => {
  it("parses markdown links", () => {
    const segs = parseAnswerSegments("See [Source](https://groww.in/foo)");
    expect(segs).toHaveLength(2);
    expect(segs[1]).toEqual({
      type: "link",
      label: "Source",
      href: "https://groww.in/foo",
    });
  });

  it("turns 'Source: <bare url>' into a clickable URL with URL as label", () => {
    const segs = parseAnswerSegments("Source: https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth");
    expect(segs.length).toBeGreaterThanOrEqual(2);
    const link = segs.find(s => s.type === "link");
    expect(link).toBeTruthy();
    if (link && link.type === "link") {
      expect(link.href).toContain("groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth");
      expect(link.label).toContain("groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth");
    }
  });
});

describe("escapeHtml", () => {
  it("escapes script tags", () => {
    expect(escapeHtml("<script>")).toBe("&lt;script&gt;");
  });
});
