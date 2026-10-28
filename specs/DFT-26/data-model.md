# Data Model: DFT-26

This feature has no persisted entities or database migrations. Its entities are
in-memory values and configuration used by the frontend utility.

## File size

- **Representation:** JavaScript `number` interpreted as bytes.
- **Valid domain:** finite, non-negative values.
- **Validation:** negative, `NaN`, positive infinity, and negative infinity
  throw `RangeError` at runtime. Static JSDoc typing exposes the numeric input
  contract to `checkJs` callers.
- **Relationships:** converted into one formatted file-size value; no storage
  or identity relationship.

## Formatted file size

- **Representation:** display-ready JavaScript `string`.
- **Units:** `B`, `KB`, `MB`, `GB`, and `TB`.
- **Conversion:** divide by 1024 per unit, choosing the largest supported unit
  that applies; values beyond TB remain in TB.
- **Precision:** no more than two decimal places, with trailing zeroes removed.
- **Boundary behavior:** zero is a non-empty byte result; exact powers of 1024
  promote to the next unit.

## Front-end type-check configuration

- **Scope:** `frontend/src/**/*.js`.
- **Required options:** `allowJs: true`, `checkJs: true`, `noEmit: true`.
- **Effect:** source diagnostics are reported by `tsc -p
  frontend/tsconfig.json`; no compiled output is created.

## State transitions

There are no persisted state transitions. A valid numeric input synchronously
transitions to formatted display text; an invalid runtime input transitions to a
`RangeError`.
