# Implementation Plan: Export and Download Vault Data

**Branch**: `DFT-11` | **Date**: 2026-10-12 | **Spec**: [./spec.md](./spec.md)

**Input**: Feature specification from `./specs/DFT-11/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

Add an authenticated, owner-scoped vault export for the metadata currently represented by
`vault.Document`. Replace the broken legacy response with a bounded, synchronous in-memory
ZIP containing a versioned JSON manifest and document data. The complete archive is built,
closed, and validated before a download response is returned; no generated export is written
to disk or retained server-side.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.11+/Django 5.2 (the repository's supported Django runtime)

**Primary Dependencies**: Django~=5.2 and Python standard library (`json`, `zipfile`, `io`, `hashlib`, `datetime`); no new runtime dependency

**Storage**: Existing Django ORM/SQLite development database; export generated in `BytesIO`, with no export storage or migration

**Testing**: Django `TestCase` via `python manage.py test`; implementation must add coverage for success, empty vault, isolation, authentication, integrity, and failure paths

**Target Platform**: Django web application on the existing Linux/server deployment

**Project Type**: Server-rendered Django web application

**Performance Goals**: Complete normal vault exports in one request; enforce a configurable maximum serialized export size/record volume so generation cannot be unbounded

**Constraints**: Build the full ZIP before sending; do not stream an unfinalized archive; no partial success; no filesystem/security-zone writes; preserve per-user authorization; no new dependency; failures must not carry attachment headers

**Scale/Scope**: Current metadata-only vault (`Document` plus related taxonomy); attachments, asynchronous workers, persistent export records, and unrelated account data are out of scope

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **PASS** — planning artifacts use the required Spec-Kit workflow; implementation must continue through tasks, analysis, implementation, and convergence.
- **PASS with implementation condition** — security controls must be respected. The export is generated only in memory and is not written under any declared zone; authorization is rechecked by the authenticated view.
- **PASS with implementation condition** — any functional implementation must include Django tests and rely on CI as the merge authority; this planning phase creates no tests.
- **PASS** — no novel runtime dependency is proposed.
- **PASS with delivery condition** — implementation is delivered through a human-reviewed pull request against protected `main`.

## Project Structure

### Documentation (this feature)

```text
specs/DFT-11/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
vault/
├── views.py                 # export generation and failure response
├── urls.py                  # authenticated export route
└── services.py              # planned serializer/archive builder boundary
templates/vault/
└── document_list.html       # visible export action and failure messaging
tests/
└── test_vault_export.py     # planned functional coverage
```

**Structure Decision**: Keep the feature in the existing `vault` Django app. Put deterministic
serialization and archive validation behind a small service boundary so the view handles
authentication/HTTP concerns, and add the export action to the existing document list. Do not
add a model, migration, worker, media directory, or persistent artifact for this scope.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | The design uses the existing Django app and standard library only. |
