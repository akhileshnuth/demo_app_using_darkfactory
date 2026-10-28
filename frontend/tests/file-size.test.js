import { describe, expect, it } from "vitest";

import { formatFileSize } from "../src/lib/file-size.js";

describe("formatFileSize", () => {
  it("formats bytes and zero", () => {
    expect(formatFileSize(0)).toBe("0 Bytes");
    expect(formatFileSize(512)).toBe("512 Bytes");
  });

  it("promotes values at unit boundaries", () => {
    expect(formatFileSize(1024)).toBe("1 KB");
    expect(formatFileSize(1024 ** 2)).toBe("1 MB");
  });

  it("rounds fractional values to two decimal places", () => {
    expect(formatFileSize(1536)).toBe("1.5 KB");
    expect(formatFileSize(123456789)).toBe("117.74 MB");
  });

  it("keeps very large values in terabytes", () => {
    expect(formatFileSize(1024 ** 6)).toBe("1048576 TB");
  });

  it("rejects negative and non-finite values", () => {
    expect(() => formatFileSize(-1)).toThrow(RangeError);
    expect(() => formatFileSize(Number.NaN)).toThrow(RangeError);
    expect(() => formatFileSize(Number.POSITIVE_INFINITY)).toThrow(RangeError);
  });
});
