# Implementation Plan: Checklists, Secure Sharing, Emergency Access & Notifications

**Branch**: `DFT-9-checklists-secure-sharing`  **Date**: 2026-10-12  **Spec**: [`./spec.md`](./spec.md)

## Summary

Bring the existing Django `checklists` surface into compliance with the approved DFT-9 specification. The repository already contains a partial implementation (`./checklists/`) and tests, so this is a gap-remediation plan rather than a greenfield app plan. The implementation must support checklist CRUD and ordering, recipient-bound invitation sharing with view/contribution permissions, designated-content emergency access with configurable safeguards and expiry/revocation, durable security events, and preference-aware in-product notifications.

No new runtime dependency is planned. Existing `accounts.User`, Django ORM, CSRF middleware, transactions, and the server-rendered template stack are reused.

## Technical Context

- **Language/runtime**: Python 3.11+, Django 5.2, SQLite for local/test use.
- **Existing integration points**: `./config/settings.py`, `./config/urls.py`, `./checklists/models.py`, `./checklists/services.py`, `./checklists/forms.py`, `./checklists/views.py`, `./checklists/urls.py`, `./templates/base.html`.
- **Existing baseline**: six partial feature models, settings, routes, templates, migration, and `./tests/test_checklists.py` exist. They currently implement direct read-only sharing and a lazy all-checklists emergency grant, which do not satisfy the approved spec.
- **Data**: extend/replace the partial model with `Checklist`, `ChecklistItem`, `ShareGrant`/invitation state, `EmergencyAccessPolicy`, `EmergencyAccessRequest`/session state, `NotificationPreference`, `Notification`, and append-only `SecurityEvent` records. Preserve valid existing data during migrations where feasible; document any destructive migration as a human-reviewed decision.
- **Authorization**: centralized service/query predicates; every read and mutation is scoped to the authenticated user and applicable grant. Unauthorized resource existence must not be disclosed.
- **Notifications**: in-product history is mandatory. External channels are out of scope until product/security approval; delivery status and failures remain durable and must not alter authorization.
- **Testing**: Django test runner, including authorization, validation, state-transition, concurrency/idempotency, notification, and regression coverage. Do not add tests in this planning phase; name them for the implementation phase.
- **Unknowns resolved in Phase 0**: permission vocabulary, invitation lifecycle, emergency policy/session states, security-event ownership, notification semantics, and scheduler/dependency boundaries are recorded in [`./research.md`](./research.md).

## Constitution Check

*GATE: evaluated before research and again after design.*

- **I — Spec-Kit completeness**: PASS for this planning run; the approved spec, research, design, and contract artifacts are produced. Tasks/implementation/convergence remain subsequent pipeline stages.
- **II — Declared security zones**: **BLOCKED pending human gate**. `./SECURITY_ZONES.md` still contains template paths and no factory zone map was found in-repository. The human workflow must reconcile `accounts/` auth/PII and the DFT-9 sensitive portions of `checklists/` with the factory map and CODEOWNERS before implementation. Agents must not write those zones.
- **III — Human-gated merge**: PASS as a delivery constraint; implementation lands through reviewed PR and CI.
- **IV — Test-first**: PASS in design; implementation must update/add Django tests before functional code is accepted.
- **V — No novel dependencies**: PASS; use Django and Python standard library only. Any exception requires human approval.

**Precondition**: resolve the Principle II mapping before implementation. This plan does not authorize agent changes to `./accounts/`, `./checklists/models.py`, `./checklists/forms.py`, `./checklists/services.py`, or `./checklists/views.py` while those paths are human-gated.

**Post-design gate**: PASS with the same blocking human precondition. The design resolves the technical unknowns without adding dependencies, defines testable authorization/state/notification contracts, and keeps retention/legal/provider decisions explicitly approval-gated rather than silently assumed.

## Phase 0 — Research

Research decisions and repository findings are in [`./research.md`](./research.md). They resolve all clarification items and identify the current partial implementation gaps, including missing reorder/title-edit paths, invitation acceptance, contribution permission, designated emergency content, expiry, notification preferences/delivery outcomes, and a dedicated security-event ledger.

## Phase 1 — Design

- [`./data-model.md`](./data-model.md): entities, relationships, constraints, validation, and state machines.
- [`./contracts/web-contracts.md`](./contracts/web-contracts.md): authenticated server-rendered routes, forms, authorization outcomes, invitation acceptance, emergency flow, preferences, notification history, and safe error behavior.
- [`./quickstart.md`](./quickstart.md): implementation-owner validation scenarios mapped to FRs and SCs.

## Implementation handoff (for the later dev task)

1. Human updates `./SECURITY_ZONES.md`, factory zone configuration, and `./.github/CODEOWNERS` (or records the approved equivalent) and identifies the authorized owners for zoned files.
2. Human-gated work updates sensitive models/services/forms/views and migrations, including invitation token handling, permission checks, emergency release controls, security-event writes, and notification delivery state.
3. Agent-eligible work may update non-sensitive URL/template/settings wiring only after the gate, without bypassing service authorization.
4. Add migrations with explicit data-preservation/backfill strategy; remove or reconcile the stray `DuplicateModel` in `./checklists/models.py` before generating migrations.
5. Add/adjust tests named in the quickstart, run `python manage.py check` and `python manage.py test`, and complete human security review.

## Project structure

```text
./specs/DFT-9/
├── plan.md
├── research.md
├── data-model.md
├── contracts/web-contracts.md
└── quickstart.md
```

Expected implementation touchpoints are `./checklists/`, `./templates/checklists/`, `./templates/base.html`, `./config/settings.py`, `./config/urls.py`, and `./tests/`; sensitive writes remain human-gated under FR-019.
