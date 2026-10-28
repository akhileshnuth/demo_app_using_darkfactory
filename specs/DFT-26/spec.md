# Feature Specification: Front-end JavaScript Type-checking and File-size Formatting

**Feature Branch**: `026-type-check-frontend-js`

**Created**: 2026-10-28

**Status**: Draft

**Input**: User description: "Ticket DFT-26: Type-check the front-end JavaScript with tsc and add a small file-size formatter"

## Clarifications

### Session 2026-10-28

- Q: Which repository scope should DFT-26 target, given that this checkout is a stack-neutral Django template with no root package.json, front-end JavaScript source, or existing file-metadata UI? → A: Keep this repository stack-neutral and add a new front-end source set, package workflow, and formatter here
- Q: What exact JavaScript source paths must tsc include, and which existing command or CI job must invoke the no-emit type check? → A: Include frontend/src/**/*.js through a new frontend/tsconfig.json with allowJs, checkJs and noEmit turned on. Run the type check directly with: tsc -p frontend/tsconfig.json
- Q: Should the formatter be delivered as a tested standalone utility, or must it be wired into a specific existing file-metadata display? → A: Standalone typed utility and tests only; integrate it when an existing caller is identified
- Q: What exact display precision and invalid-input behavior should the formatter use for fractional, negative, non-finite, and otherwise invalid values? → A: Use base 1024, round to at most two decimal places while trimming trailing zeroes, and throw a RangeError for negative or non-finite runtime inputs.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Type-check front-end JavaScript (Priority: P1)

As a maintainer, I want the front-end JavaScript checked by TypeScript so that type errors are identified consistently before a change is merged.

**Why this priority**: Catching front-end type errors is the primary purpose of the ticket and improves the reliability of every subsequent front-end change.

**Independent Test**: Run the repository's front-end type-check command against the configured JavaScript sources and verify that a clean codebase completes successfully without generating compiled output.

**Acceptance Scenarios**:

1. **Given** the front-end JavaScript source set and its type-check configuration, **When** the type-check command is run, **Then** TypeScript analyzes the intended front-end JavaScript files and reports success when no type errors exist.
2. **Given** a front-end JavaScript file containing an invalid type usage, **When** the type-check command is run, **Then** the command fails and identifies the relevant file and diagnostic instead of silently succeeding.

---

### User Story 2 - Display readable file sizes (Priority: P2)

As a front-end user or maintainer, I want file sizes rendered in a compact human-readable form so that byte counts are easy to understand wherever file metadata is shown.

**Why this priority**: The formatter is the ticket's user-facing enhancement, but it depends on the front-end remaining type-safe and can be adopted independently by callers.

**Independent Test**: Supply representative byte counts to the formatter and verify that it returns stable readable values for bytes, larger units, zero, and boundary values.

**Acceptance Scenarios**:

1. **Given** a non-negative file size in bytes, **When** it is passed to the formatter, **Then** the formatter returns a concise value with the appropriate human-readable unit.
2. **Given** a size at a unit boundary, **When** it is formatted, **Then** the formatter promotes it to the next unit using the agreed unit base and does not expose an unformatted raw byte count.
3. **Given** a zero-byte size, **When** it is formatted, **Then** the formatter returns a clear zero-size result rather than an empty value.

---

### User Story 3 - Keep the formatter safe to consume (Priority: P3)

As a front-end developer, I want the file-size formatter to have a predictable typed interface so that callers can use it without adding duplicated conversion logic or type-check exceptions.

**Why this priority**: A small, predictable interface allows the utility to be reused while keeping the new type-checking workflow effective.

**Independent Test**: Type-check a caller that imports and uses the formatter with a numeric byte count, and verify that the formatter's return value can be used as display text without additional type assertions.

**Acceptance Scenarios**:

1. **Given** a caller provides a valid numeric byte count, **When** it invokes the formatter, **Then** the call passes the front-end type check and returns display-ready text.
2. **Given** a caller attempts to use an unsupported input type, **When** the type-check command is run, **Then** the invalid call is reported as a type error.

### Edge Cases

- A size of zero is formatted as a meaningful zero-byte value.
- Sizes exactly at a unit boundary use the larger unit without unnecessary trailing precision.
- Fractional values after unit conversion are rounded or limited to a small, consistent number of display decimals so output remains compact.
- Very large non-negative values continue using the largest supported unit rather than producing an invalid or blank result.
- Negative, non-finite, or otherwise invalid inputs are rejected by the formatter's typed contract and produce a defined validation result rather than misleading file-size text.
- A type error in any configured front-end JavaScript file causes the type-check command to fail with actionable diagnostics.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The project MUST provide a repeatable type-check operation using `tsc` for the configured front-end JavaScript source set.
- **FR-002**: The type-check operation MUST check JavaScript files with TypeScript's JavaScript-checking support and MUST NOT emit compiled files as a side effect.
- **FR-003**: The type-check operation MUST include the front-end files needed to detect errors in the existing application and the new file-size formatter.
- **FR-004**: The type-check operation MUST return a failing status and actionable diagnostics when a checked front-end file contains a type error.
- **FR-005**: The project MUST provide a small reusable formatter that accepts a file size expressed in bytes and returns human-readable display text.
- **FR-006**: The formatter MUST select an appropriate size unit, including bytes and larger units, according to a consistent unit base.
- **FR-007**: The formatter MUST handle zero and unit-boundary values deterministically and keep output compact and suitable for front-end display.
- **FR-008**: The formatter MUST expose a predictable typed interface so valid consumers type-check without casts and invalid input types are caught by `tsc`.
- **FR-009**: Automated tests MUST cover the formatter's normal, zero, boundary, large-value, and invalid-input behavior, and the type-check operation MUST be covered by the project's verification workflow.
- **FR-010**: The feature MUST NOT introduce a new runtime dependency without human approval.
- **FR-011**: The feature MUST avoid writes to declared security-zone paths; any changes are limited to front-end type-check configuration, the formatter, its tests, and associated project verification configuration.

### Key Entities *(include if feature involves data)*

- **File size**: A non-negative numeric quantity representing a file's size in bytes before formatting.
- **Formatted file size**: The display-ready text containing a scaled numeric value and its selected size unit.
- **Front-end type-check configuration**: The project configuration that identifies JavaScript files to analyze, enables the required checks, and prevents emitted build artifacts.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: One documented type-check command analyzes 100% of the configured front-end JavaScript source set and exits successfully when the source is type-correct.
- **SC-002**: Introducing a deliberate type error into any checked front-end file causes the type-check command to exit non-zero and report the affected file and diagnostic.
- **SC-003**: 100% of formatter acceptance cases—zero, ordinary values, unit boundaries, large values, and invalid inputs—produce the specified deterministic result in automated tests.
- **SC-004**: The formatter returns display-ready text for every valid supported file size without requiring callers to implement unit conversion or type assertions.

## Assumptions

- The repository already has a front-end JavaScript source set and an existing package or verification workflow to which the `tsc` check can be added.
- The formatter accepts file sizes as byte counts and uses a conventional base of 1024 bytes per unit, with compact decimal output; the exact precision is not specified by the ticket and will be settled during clarification or plan review.
- The formatter's supported units are bytes, KB, MB, GB, and TB; values beyond TB remain in the largest supported unit unless project conventions require another behavior.
- Invalid values are outside the normal file-size domain; the implementation will use a deterministic, typed validation behavior rather than silently displaying an incorrect size.
- **MISSING INPUT**: The ticket does not identify the front-end entry points, current build scripts, existing TypeScript configuration, or the intended formatter call site. The work must first map the existing front-end source and verification conventions, then limit configuration and utility changes to those locations without changing unrelated behavior.
- **MISSING INPUT**: No design file, UI specification, or required example output was provided. The specification therefore defines behavior through the acceptance scenarios and assumptions above; visual formatting details remain subject to clarification.
- Existing test infrastructure is available for formatter tests, and no new runtime dependency is required.
- The feature does not require authentication, payment, PII, secret handling, or writes to any security-sensitive path.
