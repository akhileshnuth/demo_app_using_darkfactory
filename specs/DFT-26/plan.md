# Implementation Plan: Front-end JavaScript Type-checking and File-size Formatting

**Branch**: `DFT-26` | **Date**: 2026-10-28 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `./specs/DFT-26/spec.md`

## Summary

Add a standalone JavaScript frontend source set and a reproducible no-emit
TypeScript check for it. Implement the formatter as a JSDoc-typed JavaScript
utility so it is included by `frontend/src/**/*.js` and remains consumable by
JavaScript callers. Add a small Node/Vitest workflow in the frontend package
boundary without wiring the utility into the existing Django templates, which
have no current file-size caller.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: JavaScript (ES2022-compatible runtime), TypeScript compiler
for `allowJs`/`checkJs`; Node >=22 for the package test workflow

**Primary Dependencies**: TypeScript as a development-only compiler and Vitest
for formatter tests; no new runtime dependency

**Storage**: N/A

**Testing**: Vitest formatter unit tests; `tsc -p frontend/tsconfig.json`;
existing Django tests remain unchanged

**Target Platform**: Browser-oriented frontend source checked in Linux CI; Node
>=22 test runner

**Project Type**: Stack-neutral Django template with an isolated frontend
utility/tooling source set

**Performance Goals**: Formatter is O(1) and suitable for synchronous display
formatting; no application throughput target

**Constraints**: No emitted JavaScript or build artifacts from type-checking;
base 1024; at most two fractional decimals with trailing zeroes removed;
values above TB stay in TB; invalid runtime numbers throw `RangeError`;
avoid declared security zones and runtime dependencies

**Scale/Scope**: New `frontend/src/**/*.js` source set, one formatter module,
focused tests, and package/CI verification wiring only

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

* **PASS — Complete Spec-Kit pipeline:** this plan produces the required Phase
  0/1 artifacts; tasks, implementation, analysis, convergence, and human-gated
  delivery remain required before completion.
* **PASS — Security zones:** planned paths are outside `src/auth`,
  `src/payments`, and `src/customers`; no zone changes are proposed.
* **PASS — Human-gated merge:** implementation is intended for a PR against
  protected `main` with CI and human review.
* **PASS — Test-first:** formatter behavior and the type-check command will be
  covered by automated verification in the implementation phase.
* **PASS — No novel runtime dependency:** TypeScript and Vitest are
  development tooling only; no production dependency is introduced.

**Post-design re-check: PASS.** The Phase 0 decisions and Phase 1 artifacts
keep all changes outside security zones, preserve human review and CI gates,
plan tests for the functional utility, and introduce no runtime dependency.
The formatter is an internal module rather than an external API, so no
`contracts/` artifact is required.

## Project Structure

### Documentation (this feature)

```text
specs/DFT-26/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output; not created by this plan
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
frontend/
├── package.json              # frontend tool/test scripts and dev dependencies
├── package-lock.json         # reproducible frontend tooling install
├── tsconfig.json             # allowJs + checkJs + noEmit
├── src/
│   └── lib/file-size.js      # JSDoc-typed standalone formatter
└── tests/
    └── file-size.test.js     # formatter behavior and validation cases
```

**Structure Decision**: Keep the Django application and its server-rendered
templates unchanged. Add an isolated `frontend/` package because the active
checkout has no root package manifest, JavaScript source, or existing frontend
caller. The package exposes the exact check command `tsc -p
frontend/tsconfig.json` from the repository workflow and tests the standalone
utility without template integration. If the repository's eventual stack
overlay requires root-level npm scripts, those scripts may delegate to this
package, but this ticket does not apply the unrelated Node overlay to the
Django template.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | The isolated frontend package is within the existing project structure and does not add a second application or runtime service. |
