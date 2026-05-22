import { describe, expect, it } from "vitest";
import { detectPii } from "./pii";

describe("detectPii", () => {
  it("flags PAN", () => {
    expect(detectPii("my pan is ABCDE1234F")).toBe("PAN number");
  });

  it("flags email", () => {
    expect(detectPii("contact me at user@example.com")).toBe("email address");
  });

  it("allows fund questions", () => {
    expect(detectPii("What is the expense ratio of HDFC Mid Cap Fund?")).toBeNull();
  });
});
