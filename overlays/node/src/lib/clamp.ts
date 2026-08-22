/** Sample module — replace with your code. It exists so the template's
 * test suite is green out of the box, and so the factory's dev agent has
 * an existing module + test pair to mirror for style. */
export function clamp(value: number, min: number, max: number): number {
  if (min > max) throw new RangeError("min must not exceed max");
  return Math.min(max, Math.max(min, value));
}
