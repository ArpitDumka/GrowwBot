import { describe, expect, it } from "vitest";
import { extractSourceUrl, stripSourceLine } from "./extractSource";

describe("extractSource", () => {
  it("extracts Groww URL from Source: line", () => {
    const text = "NAV is 100.\nSource: https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth";
    expect(extractSourceUrl(text)).toBe("https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth");
    expect(stripSourceLine(text)).toBe("NAV is 100.");
  });
});
