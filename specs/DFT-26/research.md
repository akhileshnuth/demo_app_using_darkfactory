# Research: DFT-26

## Repository and workflow

**Decision:** Add the feature under a new `frontend/` package boundary rather
than modifying Django templates or applying `overlays/node/` wholesale.

**Rationale:** The active checkout contains Django code, no root
`package.json`, no JavaScript source, no script tags, and no file-size display.
The specification explicitly calls for a new source set and standalone utility.
The existing Node overlay is a reusable template, not an applied root workflow;
copying it into this checkout would introduce unrelated stack changes.

**Alternatives considered:**

- Wiring the formatter into `templates/vault/document_*`: rejected because no
  existing frontend caller or file-size UI exists.
- Editing `overlays/node/`: rejected because the ticket targets this checkout's
  new frontend source set, while the overlay is reference/template material.
- Depending on a globally installed `tsc`: rejected because the current
  environment has no `tsc` and reproducibility requires a locked dev tool.

## TypeScript configuration

**Decision:** Create `frontend/tsconfig.json` with `allowJs`, `checkJs`, and
`noEmit`, and include `src/**/*.js` relative to that config. Use the documented
command `tsc -p frontend/tsconfig.json`.

**Rationale:** This exactly matches the clarification and makes every checked
JavaScript source produce actionable diagnostics without generated output.
The formatter will use JSDoc annotations so its numeric input and string return
type are visible to `checkJs` consumers.

**Alternatives considered:** TypeScript source was rejected because the required
source set is JavaScript; a separate build/transpile step was rejected because
the feature requires a no-emit type check.

## Package and tests

**Decision:** Keep TypeScript and Vitest development-only in the frontend
package, with a lockfile and scripts for type checking and tests. Test the
formatter as a pure utility with Vitest.

**Rationale:** The constitution forbids unapproved runtime dependencies, while
development tooling is sufficient for static checking and automated behavior
verification. A lockfile makes installation reproducible in CI.

**Alternatives considered:** Adding a formatter runtime library was rejected as
unnecessary for a small O(1) conversion; adding a browser/UI test was rejected
because no caller exists.

## Formatter behavior

**Decision:** Export a function accepting a number of bytes and returning text.
Use units `B`, `KB`, `MB`, `GB`, and `TB` with a 1024 base. Select the largest
unit up to TB, format with at most two decimals, and trim trailing zeroes. Zero
and sub-kilobyte values remain in bytes. Negative and non-finite values throw
`RangeError`; values above TB remain scaled in TB.

**Rationale:** This is deterministic, compact, and directly resolves the
clarification. Runtime validation is still needed because JavaScript callers can
reach values that static types would normally exclude.

**Alternatives considered:** SI 1000-based units, unlimited units beyond TB,
and silent coercion of invalid values were rejected by the specification's
base, supported-unit, and validation requirements.

## Verification integration

**Decision:** Document and run the type-check script alongside formatter tests;
make the verification workflow invoke both, while preserving the existing
Django test command as a separate application check.

**Rationale:** Type-checking must fail on any invalid checked source and tests
must cover normal, zero, boundary, large, and invalid inputs. No existing root
CI workflow is present, so the frontend package workflow is the narrowest
repeatable integration point.

**Alternatives considered:** Relying only on the existing `python manage.py
test` suite was rejected because it cannot analyze JavaScript; integrating a
formatter caller into Django was rejected as out of scope.
