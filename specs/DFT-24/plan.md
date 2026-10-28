# Implementation Plan: Yarn CSS Build and Check Scripts

**Branch**: `DFT-24` | **Date**: 2026-10-28 | **Spec**: [./spec.md](./spec.md)

**Input**: Feature specification from [./spec.md](./spec.md)

## Summary

Add a dedicated `./frontend/package.json` package-script interface for
building, checking, and verifying CSS. Implement the operations in
`./frontend/scripts/build-css.js` using only Node built-ins: discover and sort
all `./frontend/css/*.css` files with `base.css` first, validate balanced curly
braces, and write the joined result to `./frontend/dist/app.css`. Preserve
`./static/css/base.css`, the existing npm overlay, and CI workflows.

## Technical Context

**Language/Version**: JavaScript on Node.js >=22

**Primary Dependencies**: Node built-in `node:fs` and `node:path`; no new third-party packages

**Storage**: Filesystem CSS sources and generated CSS output

**Testing**: Existing Vitest/Node test conventions; implementation phase must add focused functional tests

**Target Platform**: Cross-platform Node/Yarn development and CI environments

**Project Type**: Repository build utility exposed through a frontend package manifest

**Performance Goals**: Deterministic processing of the repository's small CSS source set; no special throughput target

**Constraints**: No third-party dependency; propagate filesystem and validation failures; do not change CI, npm workflow, templates, or `./static/css/base.css`

**Scale/Scope**: One frontend manifest, one Node utility, frontend CSS source/output directories, and functional tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Spec pipeline:** PASS — this plan records the Plan phase; later work must complete Tasks, Analyze, Implement, Converge, and Done.
- **Security zones:** PASS — planned paths are package/build/CSS paths outside the declared auth, payments, and PII zones.
- **Human-gated merge:** PASS — delivery must be a pull request to protected `main` with human review and passing CI.
- **Test-first:** PASS with implementation follow-up — the dev phase must add tests for functional script behavior; this planning phase creates no tests.
- **Dependency approval:** PASS — the design uses only Node built-ins and adds no runtime or dev dependency.

No gate violations require complexity justification.

## Project Structure

### Documentation (this feature)

```text
./specs/DFT-24/
├── plan.md              # This plan
├── research.md          # Phase 0 research
├── data-model.md        # Phase 1 entity and filesystem contracts
├── quickstart.md        # Phase 1 validation guide
└── tasks.md             # Later Phase 2 output; not created here
```

No `contracts/` artifact is needed: this is an internal package-script and
filesystem utility, not a public API or service interface.

### Source Code (repository root)

```text
./frontend/
├── package.json                 # Yarn script entry points
├── css/
│   └── base.css                 # Frontend build source, copied from existing CSS without altering it
├── scripts/
│   └── build-css.js             # Build and brace-check implementation
└── dist/
    └── app.css                  # Generated output, not source-controlled

./static/css/base.css            # Existing application stylesheet; unchanged
./tests/                         # Existing project tests plus implementation-phase coverage
```

**Structure Decision**: Use a self-contained frontend package for CSS tooling.
The backend Django/static layout remains unchanged; the generated frontend
artifact is isolated under `./frontend/dist/` and is ignored by the existing
repository `dist/` rule.

## Complexity Tracking

No constitution violations require a complexity exception. The design stays
within the existing project structure and introduces no dependency or service
boundary.
