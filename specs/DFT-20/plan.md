# Implementation Plan: Repository Ignore Rules for Database, Uploads, and Secrets

**Branch**: `DFT-20` | **Date**: 2026-10-12 | **Spec**: `./specs/DFT-20/spec.md`

**Input**: Feature specification from `./specs/DFT-20/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

Extend the existing root `./.gitignore` so the configured SQLite database and
sidecars, the repository-local `./private_documents/` upload tree, and the
already-established local environment/credential patterns stay untracked.
Retain the `./.env.example` exception. Because the clarification explicitly
includes secret remediation, update `./config/settings.py` to obtain
`SECRET_KEY` from the environment rather than committing a development value;
credential rotation/revocation of the historical value is an operational,
human-reviewed release action and cannot be achieved by Git ignore rules.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python (repository Django application; runtime version to be confirmed by existing project tooling)

**Primary Dependencies**: Django 5.2.18; Git ignore semantics; no new runtime dependencies

**Storage**: SQLite at `./db.sqlite3`; private file storage defaults to `./private_documents/` and may be externally overridden

**Testing**: Existing Django test suite plus planned Git command validation; add focused regression coverage for ignore decisions and environment-backed settings

**Target Platform**: Git checkout on the project development/deployment platforms; current factory validation runs on Linux

**Project Type**: Django web application

**Performance Goals**: No runtime performance impact; Git checks should be immediate for the small repository rule set

**Constraints**: Root-anchored rules must avoid unrelated nested files; do not add database/upload/secret fixtures; do not untrack committed files; external upload roots are outside repository scope

**Scale/Scope**: One existing root ignore file, one settings assignment, and focused validation/test documentation; no migrations or new packages

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **PASS — Complete Spec-Kit pipeline:** This plan is the required Plan phase; subsequent Tasks, Analyze, Implement/Converge, and Done phases remain required.
- **PASS — Security zones:** Planned paths (`./.gitignore`, `./config/settings.py`, and planned tests/documentation) are outside the declared `src/auth`, `src/payments`, and `src/customers` prefixes. No writes are planned inside `payments`, `auth`, or `pii` zones. The repository's zone declarations/factory mirror remain a governance concern, not a DFT-20 file change.
- **PASS — Human-gated merge:** Delivery must be a reviewed PR to protected `main` with CI passing. The exposed historical development key must be rotated/revoked by the responsible human/deployment owner; code changes cannot perform that external operation.
- **PASS — Test-first:** The settings change is functional and therefore requires focused tests; ignore-only behavior is validated with `git check-ignore` and status checks. Tests are named in the plan but are not created in this planning phase.
- **PASS — Dependencies:** No new runtime dependency is proposed.

No gate violations require complexity justification.

## Project Structure

### Documentation (this feature)

```text
./specs/DFT-20/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

No `contracts/` artifact is needed: this feature exposes no application API,
CLI protocol, or external system interface.

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
./.gitignore                  # Extend existing root ignore rules
./config/settings.py          # Read SECRET_KEY from the environment
./tests/test_repository_ignore.py  # Planned focused regression coverage
./tests/                      # Existing Django test suite remains authoritative
```

**Structure Decision**: Keep the existing single Django project layout. The
repository policy belongs in the root ignore file, runtime secret loading in
`config/settings.py`, and functional regression checks in the existing
`tests/` package. No upload or database fixture is committed.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | No constitution violation identified |

## Phase 0: Research Summary

Research is complete in `./specs/DFT-20/research.md`. It resolves the
previously missing path conventions from the live settings and existing ignore
rules: four root SQLite artifacts, root `private_documents`, `.env` with the
`.env.example` exception, and the explicitly named credential patterns already
supported by the repository.

## Phase 1: Design Summary

The design artifacts are `./specs/DFT-20/data-model.md` and
`./specs/DFT-20/quickstart.md`. There are no external interface contracts.

## Post-Design Constitution Re-check

- **PASS:** Design changes remain outside declared security-zone prefixes.
- **PASS:** The plan names tests for the functional settings change and uses
  Git-native validation for ignore behavior.
- **PASS:** No dependency, migration, fixture, or committed secret content is
  introduced.
- **PASS:** Existing tracked files are not removed or untracked by ignore rules;
  historical key rotation is explicitly a separate human operational action.
