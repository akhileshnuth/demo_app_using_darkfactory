// Sample test — the factory's dev agent reads an existing test before
// writing new ones and mirrors its imports and structure. Keep at least
// one real test in this style.
import { describe, expect, it } from "vitest";

import { clamp } from "../src/lib/clamp";

describe("clamp", () => {
  it("passes through in-range values", () => {
    expect(clamp(5, 0, 10)).toBe(5);
  });

  it("clamps below and above", () => {
    expect(clamp(-1, 0, 10)).toBe(0);
    expect(clamp(11, 0, 10)).toBe(10);
  });

  it("refuses an inverted range", () => {
    expect(() => clamp(5, 10, 0)).toThrow(RangeError);
  });
});
