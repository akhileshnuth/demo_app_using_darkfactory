# DFT-9 Research & Design Decisions

**Phase 0 output** — resolves all `NEEDS CLARIFICATION` items from the Technical
Context (app structure, storage, testing, notification/timeout mechanics) and records
best-practice decisions for the checklists/sharing/emergency/notifications feature.
Each entry follows *Decision / Rationale / Alternatives considered*.

Date: 2026-09-09

---

## R1. Where the feature lives: a single `checklists` Django app

**Decision**: Implement all four capabilities in **one new first-party app,
`checklists/`**, at the repo root (flat Django layout from DFT-7). `accounts/` and
`dashboard/` are unchanged; `config/urls.py` gets `include("checklists.urls")` and
`config/settings.py` adds `"checklists"` to `INSTALLED_APPS`. The shared shell
(`templates/base.html`) is lightly edited to add the checklist + notifications nav
links and the header unread badge; a `context_processors.py` under `checklists/`
supplies the unread count.

**Rationale**: The four capabilities are cohesive (sharing/emergency/notifications all
revolve around checklists) and share one data model and one policy layer
(`services.py`). One app keeps the review surface small, mirrors the DFT-7/DFT-8
one-app-per-concern convention, and — crucially — keeps every new model/view off the
zoned `accounts/` auth/PII paths (Constitution Principle II).

**Alternatives considered**: Several small apps (`checklists`, `sharing`, `emergency`,
`notifications`) — over-splits a single domain and cross-couples their models; a
shared `notifications` app reused by future features is defensible but unnecessary at
this scale. Merging into `dashboard/` — muddies the shell's responsibility and is not
feature-isolated.

## R2. Models use the existing `accounts.User` directly

**Decision**: All new entities reference `settings.AUTH_USER_MODEL` (`accounts.User`)
via `ForeignKey`/`OneToOneField`, using `related_name` throughout. No change to the
User/Profile models, no new user fields, no separate "viewer" role model.

**Rationale**: FR-018/FR-019/FR-020 reuse the existing auth/identity; the spec's
Assumptions say DFT-7's auth is reused as-is. Clear of the zoned `accounts/` surface.

**Alternatives considered**: Adding "is_emergency_contact" flags on `User` — couples
feature state into the zoned auth model and pollutes it; a dedicated relationship
entity (`EmergencyContact`) is cleaner and matches the spec's Key Entities. A
custom `Through`/role model for shares beyond `ChecklistShare` — unnecessary today
(v1 is owner/recipient only).

## R3. Checklist ownership & item ordering

**Decision**: `Checklist.owner = FK(User)`. `ChecklistItem` holds `position`
(unsigned `PositiveIntegerField`, 0-based ordering) with a unique-together
(`checklist`, `position`); items ship with explicit ordering by `position`, and add is
`max(position)+1`. Item text is a required `CharField` (≤ 200 chars). Completion is a
`BooleanField` (`is_complete`, default False).

**Rationale**: FR-003 implies ordering/position (the spec lists "order/position" as a
ChecklistItem attribute); a stable integer position is the simplest durable order.
Toggle = flip a boolean; stats = `count()` of complete vs total.

**Alternatives considered**: Reordering UI with drag/drop — not in scope (spec lists
position but no reorder interaction; keep payload minimal). A float-weight ordering —
over-engineering for server-rendered v1.

## R4. Sharing: read-only recipient model via `ChecklistShare`

**Decision**: `ChecklistShare(checklist, recipient, status)` with `status` in
{active, revoked}; one row per (checklist, recipient), enforced by
`UniqueConstraint(checklist, recipient)`. **Recipients are read-only**: authorization
for edits always requires `owner`, never a share. A shared view shows "Shared by
[owner]" and the edit/delete controls are simply not rendered (and a `services`
authorization guard rejects any direct edit POST). Revocation sets `status="revoked"`
(history-preserving) rather than deleting the row.

**Rationale**: FR-005/007/008 require share-by-email, read-only enforcement, and
revoke. A status column preserves history and makes "already revoked, reshare" an
update rather than a recreate, simplifying the "already shared" edge case. Enforcing
read-only at the authorization layer (not just the UI) satisfies SC-006 (no data leaks
via direct URL/action).

**Alternatives considered**: Hard-deleting share rows on revoke — loses history and
makes the notification "access revoked" target harder to track. Permission tables /
per-object ACLs — over-engineered for owner-vs-recipient sharing.

## R5. Designating an owner as their own emergency contact is rejected

**Decision**: `EmergencyContact.owner` must differ from `EmergencyContact.contact`
(validated in the form/model `clean`); a self-designation fails with an inline error.

**Rationale**: Spec edge case "user attempts to designate themselves as their own
emergency contact" — granting yourself emergency access to your own checklists is
meaningless.

**Alternatives considered**: Allowing it (no-op) — silently confusing; rejecting with a
clear message is the specified expectation.

## R6. Emergency access scope is all-of-owner's-checklists

**Decision**: `EmergencyAccessRequest` holds `status` in
{pending, approved, denied, auto_granted}; approval/auto-grant grants **viewer access
to every** `Checklist` owned by the target owner (*currently active* ones; a shared
view surfaces them), as the spec's Assumptions state no per-checklist granularity in
v1. Access is viewer-scope only (read-only), matching FR-007.

**Rationale**: Spec explicitly: "Emergency access applies to ALL of the owner's
checklists." Simplest correct v1 model; no per-checklist rows to manage.

**Alternatives considered**: Per-checklist emergency rows / a per-checklist grant —
explicitly out of scope. Emergency grants creating persistent `ChecklistShare` rows —
different concept; emergency is a time-boxed, all-or-nothing grant with its own
lifecycle (cancelled/revoked on contact removal), kept separate from regular shares.

## R7. Removing an emergency contact cancels pending requests and revokes grants

**Decision**: Deleting an `EmergencyContact` cascades: in-flight
`EmergencyAccessRequest` rows from that (owner, contact) pair are cancelled (status →
`cancelled` — an added state) and any already-granted emergency viewer access is
revoked (pending/approved/auto-granted → cancelled) in the same transaction. Both owner
and contact are notified of the revocation where applicable.

**Rationale**: Spec acceptance 6 of User Story 3 ("pending requests are cancelled and
any previously granted emergency access is revoked"). History-preserving via a
`cancelled` status rather than hard-delete keeps an audit trail.

**Alternatives considered**: Hard-deleting request rows — loses audit history of
granted access.

## R8. The 72 h auto-grant: a lazy, poll-on-read check (no background daemon)

**Decision**: No scheduler, no celery, no cron. When an `EmergencyAccessRequest` with
status `pending` is inspected — specifically (a) when the requesting contact views
their access status, or (b) when any code path reads the request for the 
owner/contact — the system compares `request.timeout_deadline` (computed at creation
as `created_at + settings.CLA_OK_EMERGENCY_AUTO_GRANT_HOURS`, default 72) against
`timezone.now()`. If past, the request is atomically transitioned `pending →
auto_granted` (guarded by a conditional update so concurrent checks apply the grant
exactly once), and both parties are notified. The "grace" is thus evaluated eagerly
exactly when something needs to know.

**Rationale**: SC-003 ("auto-grant triggers exactly at the configured timeout with
zero manual intervention") is satisfied without a job framework — a genuine need only
arises when someone asks, so eager-on-read is correct and dependency-free. The
conditional-update guard keeps the grant idempotent under concurrent reads (spec edge
case: "auto-grant occurs while a manual approval is in progress" — addressed in R9).

**Alternatives considered**: Celery beat / cron / systemd timer for a job — introduces
a novel runtime dependency (violates Principle V without approval) and infrastructure a
server-rendered, single-SQLite app doesn't otherwise need. Evaluating the timeout on
every request via middleware — heavier and more invasive than evaluating on
request-read.

## R9. Race: auto-grant vs manual approval in progress

**Decision**: The transition is a **state machine with a single atomic step**. All
transitions are conditional `UPDATE ... WHERE status = <expected>` semantics (Django
`QuerySet.filter(status=...).update(...)` or `select_for_update` in a transaction):
- `pending → approved` (owner click)
- `pending → denied` (owner click)
- `pending → auto_granted` (home on read)
- `pending → cancelled` (contact removed)
- any-of-{pending,approved,auto_granted} → `cancelled` (contact removed)
Whichever transition wins the race commits; the loser's conditional update matches zero
rows and is simply a no-op (or shows a "this request was already resolved" message).
Thus an auto-grant and a manual denial can never both clinch — exactly one final state
results.

**Rationale**: Spec edge case explicitly. A guarded compare-and-set is the smallest
correct concurrency model.

**Alternatives considered**: Advisory row-locks everywhere — heavier and redundant;
last-writer-wins — can produce contradictory notifications (approved *and* denied).

## R10. Notification system: a `Notification` entity + `services.notify()` helper

**Decision**: `Notification(recipient, type, message, is_read, created_at,
related_checklist/share/request nullable FK)`. Types: `share` (received),
`revocation` (share revoked), `emergency_request`, `emergency_response`
(approval/denial/auto-grant/revocation). A single `services.notify(...)` creates one
row per recipient. Unread count = `recipient.count(is_read=False)` — used by a context
processor for the header badge (FR-016). Mark-one-read sets `is_read=True`; "mark all
read" is a single bulk update; "clear all" is a bulk delete for the recipient. Clicking
a notification navigates to the related context via a redirect resolved from its
`related_*` reference.

**Rationale**: FR-014/015/016 + SC-004/007. An in-app table is the simplest event log,
needs no message broker, and the badge/read-state all derive from one query. Message-
template composition is kept in `services.py`.

**Alternatives considered**: `django.contrib.messages` for everything — those are
one-shot flash messages tied to a request cycle, not persistent, queryable,
per-recipient notifications with timestamps and read state; unsuitable for FR-014.
Signal/celery fan-out — no. A separate notification app reused by future features —
reasonable long-term, but this ticket's notifications are checklists-centric; a
generic app can be extracted later without changing the row model.

## R11. Notification overflow (1000+ unread) is handled

**Decision**: No cap on stored rows (FR-018 persists them); the header badge shows the
raw count but the notification-center **list** is paginated (e.g. 50/page, newest
first) so a very large inbox stays usable, and "clear all" / "mark all read" act on the
whole set via efficient bulk queries rather than iterating pages.

**Rationale**: Spec edge case "notification overflow (1000+ unread)". Persist without
loss; paginate for display; bulk operations for scale.

**Alternatives considered**: A hard cap that deletes old notifications — loses data
and contradicts FR-018's persist-everything intent.

## R12. Deleting a shared checklist & owner email change / account deactivation

**Decision**:
- **Owner deletes a shared checklist** (FR / acceptance): deleting the `Checklist`
  cascades to its items and shares; recipients are notified of the deletion/revocation
  so the shared item disappears from their lists (spec edge case "owner deletes a
  checklist that has been shared with others"). `ChecklistShare.checklist` uses
  `on_delete=CASCADE`.
- **Owner changes email** (spec edge case): email is the login identifier and shares
  reference `recipient` by FK `User`, not by email string — so a later email change
  (no change-email UI in scope, but conceptually) keeps relationships intact. No action
  needed; documented.
- **Account deactivation** (spec edge case): not in this ticket's UI scope; at the data
  layer, shares/emergency contacts reference `User` FKs so a deactivated `is_active`
  user's grants remain structurally valid but the read-only access guard can add an
  `is_active` check on both requester and recipient to keep access safe. Documented for
  the implementer; no schema impact.

**Rationale**: FK-based referencing keeps identity relationships stable; cascade delete
plus notification matches the specified behaviors.

**Alternatives considered**: Referencing recipient by email string — breaks on email
change; rejecting share with a deactivated account — sensible guard, kept minimal.

## R13. Security-zone mapping extension (Constitution Principle II)

**Decision**: Record the full real sensitive surface and instruct the implementer to
sync `SECURITY_ZONES.md` and the factory zone map before writing the feature. The new
`checklists/` data (sharing relationships, emergency contacts, emergency access
requests, notification content) is **PII** — personal/relationship data — and its
models/views/forms live in the new `checklists/` app:

| Actual path | Zone name | Why |
|---|---|---|
| `accounts/models.py` (User), `accounts/forms.py`, `accounts/views.py`, `accounts/urls.py` | `auth` | Session/authentication logic (from DFT-7 R12) |
| `accounts/models.py` (Profile), `accounts/forms.py` (ProfileForm), dashboard header display name | `pii` | Display name (personal data) — DFT-7 R12 |
| `checklists/models.py` (ChecklistShare, EmergencyContact, EmergencyAccessRequest, Notification), `checklists/views.py`, `checklists/forms.py`, `checklists/services.py` | `pii` | Sharing relationships, emergency contacts, emergency request/notification content (personal/relationship data) |

Required implementation step: update `SECURITY_ZONES.md` to these real paths and mirror
them into the factory zone map (`FACTORY_ZONES` / `agentguard/policies/zones/zones-v0.json`)
**before** writing the checklists code. Until updated, the factory config (still
`src/...`) matches nothing and no writes are denied; per Principle II that "unmapped
sensitive surface" state must not be silently assumed. The implementer must reconcile
the PR plan with the fact that, once mapped, agent writes into these zoned paths are
denied and those files become human work.

**Alternatives considered**: Structuring the feature's models under `accounts/` to reuse
an existing conceptual zone — rejected (looks configured but `accounts` is not an actual
factory zone row either, and it couples feature code into the auth app). Leaving zones
unamended and proceeding — violates Principle II.

---

## Dependency & integration notes

- **Django built-ins used**: `django.contrib.auth` (User, `LoginRequiredMixin`,
  `request.user`), `django.contrib.messages` (non-critical, optional UI flash),
  `django.contrib.staticfiles`, `django.contrib.admin` (dev convenience registrations).
- **No third-party runtime packages**: `requirements.txt` stays `Django~=5.2`.
- **Integrations**: none external — self-contained server-rendered app (SQLite, local
  templates, bundled static). No email/SMS/push, no background jobs, no REST API.
- **Cross-app**: consumes `settings.AUTH_USER_MODEL` from `accounts`; renders inside
  the `dashboard`/`base.html` shell; `config/urls.py` + `config/settings.py` wiring.
