# DFT-9 Research Decisions

**Date**: 2026-10-12  **Source**: [`./spec.md`](./spec.md)

## R1 — Extend the existing Django surface, do not create a parallel app

**Decision**: Retain `./checklists/` and its server-rendered Django integration, correcting it in place. Reuse `accounts.User`, existing authentication, CSRF middleware, ORM transactions, and the current shell.

**Rationale**: The repository already has models, routes, templates, migration, and tests. A parallel implementation would duplicate authorization and increase migration risk.

**Alternatives considered**: New micro-apps or a REST API; rejected because the approved feature has no API requirement and the existing app is the established integration point.

## R2 — Explicit permissioned, recipient-bound shares

**Decision**: A share grant records owner/inviter, intended recipient, permission (`view` or `contribute`), status, issued/accepted/revoked timestamps, and invitation expiry. Generate a high-entropy single-use invitation token, store only its hash, and bind acceptance to the authenticated intended user. Access begins only after valid acceptance.

**Rationale**: Direct email lookup and immediate access do not satisfy FR-003–FR-006 or the forwarded/expired/duplicate invitation edge cases. Contribution requires service-layer authorization on every item mutation and attribution.

**Alternatives considered**: Anonymous links, immediate direct grants, owner-only editing; all fail an approved scenario or assumption.

## R3 — Conflict-safe checklist editing and ordering

**Decision**: Keep stable item positions but expose explicit reorder and title-edit operations. Validate title/item content before persistence. Use an item version or update timestamp in mutation forms/services and return a conflict outcome instead of silently overwriting a concurrent edit; record contributor attribution.

**Rationale**: The existing code lacks reorder/title-edit and uses owner-only last-write-wins behavior, while FR-001/002/017/018 require persistence and conflict communication.

**Alternatives considered**: Client-only drag/drop or unconditional last-write-wins; rejected because they do not provide a durable server-side order or conflict signal.

## R4 — Emergency policy and time-bounded session state

**Decision**: Model an owner policy with designated checklist/item content, eligible contacts, configurable verification, approval/waiting rule, duration, and revocation settings. Model requests and released sessions separately with guarded transitions (`pending`, `approved`, `denied`, `expired`, `revoked`, `cancelled`, as applicable). Access checks enforce designated content and active session expiry on every request.

**Rationale**: The current all-checklists lazy 72-hour grant cannot satisfy FR-007–FR-010. A policy/session model makes release scope, expiry, revocation, and “owner unavailable” safeguards explicit and auditable.

**Alternatives considered**: One implicit request status, all-owner-checklist access, or a hard-coded timeout; rejected because each loses required scope/control semantics. A scheduler is not assumed; if exact-time notification is required, use an approved deployment scheduler or explicitly document request-driven reconciliation.

## R5 — Append-only security events

**Decision**: Add a dedicated `SecurityEvent` record for actor, event category/action, target references, outcome, timestamp, and minimal safe metadata. Write state change, event, and mandatory in-product notification in one transaction. Record denials, expirations, revocations, conflicts, and delivery outcomes as well as successes.

**Rationale**: Existing `accounts.ActivityLog` is not a confirmed DFT-9 audit contract and current code records only selected actions. Notifications are not an audit trail.

**Alternatives considered**: Application logs or notification rows; rejected because they are not durable, queryable, complete security records.

## R6 — Durable notification preferences and delivery outcomes

**Decision**: Store optional category/channel preferences separately from mandatory security categories. Store in-product notifications with safe actor/action/checklist reference, timestamp, read state, channel, delivery status, and sanitized failure details. Preserve history even when a checklist/share is deleted by nullable references plus safe snapshots.

**Rationale**: Satisfies FR-013–FR-016 and ensures delivery failure cannot change authorization. In-product history is the first-release channel; external delivery requires approval.

**Alternatives considered**: `django.contrib.messages`, destructive “clear all,” or synchronous external sends; rejected because they lose history or couple delivery to access decisions.

## R7 — Security-zone gate is blocking

**Decision**: Before implementation, a human must reconcile `./SECURITY_ZONES.md`, factory zone configuration, and CODEOWNERS for actual `accounts/` auth/PII and sensitive `checklists/` paths. No agent implementation writes are authorized by this plan.

**Rationale**: Constitution Principle II and FR-019 explicitly make auth/PII work human-gated. Current declarations are template defaults and no repository factory map was found.

**Alternatives considered**: Proceeding under stale mappings; rejected because enforcement would not reflect actual sensitive surfaces.

## R8 — No new runtime dependency

**Decision**: Use Django constraints, transactions, pagination, CSRF, standard-library token hashing, and the bundled test runner. Do not add Celery, Redis, DRF, or provider SDKs.

**Rationale**: Preserves Principle V and keeps local/test validation self-contained.

**Alternatives considered**: Task queues for scheduled expiry/delivery; deferred until separately approved and specified.
