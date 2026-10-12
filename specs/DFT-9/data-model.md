# DFT-9 Data Model

## Entities

### Checklist
Owner, title, lifecycle state, created/updated timestamps. Has ordered `ChecklistItem` rows and selected emergency-designation rows. Owner-only deletion; protected references use safe retention behavior for audit/notification history.

### ChecklistItem
Checklist FK, validated content, stable order key, completion state, optimistic version/update timestamp, created/updated timestamps, and last-update actor. Unique ordering within a checklist; reorder is transactional.

### ShareGrant
Checklist, owner/inviter, intended recipient, permission (`view`/`contribute`), status (`invited`, `active`, `revoked`, `expired`), issued/accepted/revoked/expiry timestamps, and invitation token hash/usage metadata. Unique active grant per checklist/recipient/permission as defined by product policy.

### EmergencyAccessPolicy
Owner, enabled state, designated checklist/item content, eligible contacts, verification method/configuration, approval/waiting condition, session duration, revocation rules, and timestamps. Policy changes invalidate pending release of removed content.

### EmergencyAccessRequest
Policy, owner, requester, status (`pending`, `approved`, `denied`, `expired`, `revoked`, `cancelled`), submitted/decided/expired timestamps, decision actor, and safe reason metadata. Guard transitions atomically. Released access is represented by an expiring session/grant so each access check can enforce duration and revocation.

### NotificationPreference
User, optional category/channel enablement, updated timestamp. Mandatory security categories cannot be disabled.

### Notification
Recipient, category, safe actor/action text or template key, checklist reference/safe snapshot, related grant/request/event, channel, delivery status (`queued`, `delivered`, `failed`), failure metadata, read state, and timestamp. User-scoped queries only; history is not authorization state.

### SecurityEvent
Append-only actor (nullable for system action), target type/IDs, action/category, outcome, timestamp, request correlation ID, and minimal sanitized metadata. No checklist contents, credentials, raw tokens, or unnecessary PII. Retention/deletion policy is a required product/security clarification before production rollout.

## Relationships

`User 1:N Checklist`; `Checklist 1:N ChecklistItem`; `Checklist 1:N ShareGrant`; `User 1:N ShareGrant` as recipient/inviter; `User 1:N EmergencyAccessPolicy`; policies relate to contacts and designated checklist/items; `EmergencyAccessRequest` belongs to policy/requester/owner; notifications reference recipients and nullable targets; security events reference actors and safe target identifiers.

## Validation and invariants

- Titles/items reject blank, oversized, unsupported content and preserve the last valid version.
- Every share invitation is bound to one intended authenticated recipient, one checklist, one permission, one expiry, and one single-use token.
- Owners cannot share to themselves; unknown/ineligible recipients are rejected without metadata leakage.
- `view` cannot mutate; `contribute` may mutate only explicitly allowed items and must attribute the actor.
- Emergency access requires policy eligibility and configured verification/release conditions; only designated content is exposed.
- Expired/revoked/denied/cancelled grants fail closed. Repeated requests are rate-limited/idempotent and audited.
- Notification preferences suppress only optional categories; mandatory security notices are always recorded and exposed in-product.
- State changes, security events, and mandatory notifications commit atomically where they share the local database.

## State transitions

Share: `invited → active → revoked/expired`; invalid/used invitations never activate.

Emergency request: `pending → approved/denied/expired/cancelled`; approved release creates `active session → expired/revoked`. All transitions use compare-and-set/transaction guards and emit one event.

Item: `incomplete ↔ complete`; edit/reorder requires current version and otherwise returns a conflict outcome.
