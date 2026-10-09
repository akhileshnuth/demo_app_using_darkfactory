# Implementation Plan: Fix Checklists Crash and Remove Test Files

**Branch**: `DFT-23` | **Date**: 2026-10-09 | **Spec**: [./spec.md](./spec.md)

## Summary

Restore the six checklist-domain models currently referenced by the application
but absent from `./checklists/models.py`, matching the existing migration and
DFT-9 data model. Delete the eight tracked files classified as tests, retaining
test configuration and non-test source. Do not add defensive behavior, unrelated
edits, or a migration unless Django reports a genuine schema difference.

## Technical Context

**Language/Version**: Python 3.x; Django 5.2 (`./requirements.txt`)
**Primary Dependencies**: Django ORM, auth, forms, generic views
**Storage**: Django relational database; schema in `./checklists/migrations/0001_initial.py`
**Testing**: Django checks and migration drift check; existing test suite is removed by the ticket
**Target Platform**: Linux-hosted server-rendered Django web application
**Project Type**: Django web application
**Performance Goals**: Preserve existing checklist query and rendering behavior
**Constraints**: Exact migration/model compatibility; minimum change; no new dependencies; no security-zone writes
**Scale/Scope**: One model module plus deletion of eight tracked test files; all checklist consumers

## Constitution Check

- **Spec-Kit completeness**: PASS for planning; all Phase 0/1 artifacts are produced.
- **Security zones**: PASS; planned paths are outside declared `src/auth`, `src/payments`, `src/customers` prefixes.
- **Human-gated merge**: PASS as a delivery constraint; implementation lands through reviewed PR/CI.
- **Test-first**: CONSTRAINED by the approved requirement to delete all test files; use checks and scope inspection, add no tests.
- **Dependencies**: PASS; no runtime dependency changes.

## Project Structure

```text
checklists/
├── models.py                 # restore six runtime models and helpers
├── services.py               # existing consumers; unchanged
├── views.py                  # existing route consumers; unchanged
└── migrations/0001_initial.py # authoritative existing schema
accounts/, dashboard/, vault/ # existing apps; test modules deleted only
```

**Structure Decision**: Single Django project with checklist domain in
`./checklists`. Runtime restoration is confined to `./checklists/models.py`; the
cleanup scope is determined from tracked test naming conventions.

## Implementation Phases

### Phase 0 — Research

Use `./research.md` to reconcile the migration, DFT-9 model contract, and all
runtime imports/usages. Confirm the exact eight tracked test paths and verify no
planned path is in a declared security zone.

### Phase 1 — Design

Use `./data-model.md` for entity/relationship details,
`./contracts/web-contracts.md` for the preserved server-rendered interface, and
`./quickstart.md` for validation. No implementation code or tests are created by
this plan.

## Complexity Tracking

None. The approved scope requires no architectural complexity or new dependency.

## Post-Design Constitution Re-check

- **Spec-Kit completeness**: PASS — `research.md`, `data-model.md`,
  `contracts/web-contracts.md`, and `quickstart.md` are present; implementation
  tasks remain intentionally out of scope for this planning command.
- **Security zones**: PASS — the model and deletion paths remain outside the
  declared security prefixes, and the plan adds no zoned write.
- **Human-gated merge**: PASS — the quickstart requires diff review and CI-style
  checks before delivery.
- **Test-first**: ACCEPTED EXCEPTION — the specification explicitly requires
  deleting all test files and forbids adding tests; validation is limited to
  checks, migration drift, runtime smoke scenarios, and scope inspection.
- **Dependencies**: PASS — no dependency or configuration changes are planned.
