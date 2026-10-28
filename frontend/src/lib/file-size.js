const BYTES_PER_UNIT = 1024;
const UNITS = ["Bytes", "KB", "MB", "GB", "TB"];

/**
 * Format a non-negative file size using binary units.
 *
 * @param {number} bytes
 * @returns {string}
 */
export function formatFileSize(bytes) {
  if (!Number.isFinite(bytes) || bytes < 0) {
    throw new RangeError("File size must be a finite, non-negative number");
  }

  let unitIndex = 0;
  let value = bytes;
  while (value >= BYTES_PER_UNIT && unitIndex < UNITS.length - 1) {
    value /= BYTES_PER_UNIT;
    unitIndex += 1;
  }

  const displayValue = Number(value.toFixed(2));
  return `${displayValue} ${UNITS[unitIndex]}`;
}
