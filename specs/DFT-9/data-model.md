# DFT-9 Data Model

**Source**: `/specs/DFT-9/spec.md` § Key Entities + FR-001…FR-020

Decisions underlying this model are in [`/specs/DFT-9/research.md`](../research.md):
single `checklists` app (R1), reuse of `accounts.User` (R2), share read-only + revoke
as status (R4), emergency all-or-nothing scope (R6), contact-removal cancels/revokes
(R7), lazy auto-grant + guarded state machine (R8/R9), notification entity (R10).

All new entities live in the new `checklists` app and reference
`settings.AUTH_USER_MODEL` (`accounts.User`) directly. `accounts/` is not modified.

---

## Entities

### 1. Checklist — `checklists.models.Checklist`

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `owner` | `ForeignKey(User)` | `on_delete=CASCADE`, `related_name="checklists"` | FR-020: owner-only management |
| `title` | `CharField` | `max_length=140`, required | FR-002 create-with-title |
| `created_at` | `DateTimeField` | `auto_now_add` | Key Entities |
| `updated_at` | `DateTimeField` | `auto_now` | Key Entities |

**Relations**: one-to-many `ChecklistItem` (`related_name="checklist"`),
one-to-many `ChecklistShare` (`related_name="checklist"`). Ordering `["-updated_at"]`
for list display; `["created_at"]` for stable IDs.

**Derived**: `item_count = items.count()`, `completed_count = items.filter(is_complete=True).count()`,
`completion_percentage` (0 when no items), `shared_with` (active shares).

### 2. ChecklistItem — `checklists.models.ChecklistItem`

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `checklist` | `ForeignKey(Checklist)` | `on_delete=CASCADE`, `related_name="items"` | FR-003 |
| `text` | `CharField` | `max_length=200`, required | Edit target (acceptance 5) |
| `is_complete` | `BooleanField` | `default=False` | Toggle (acceptance 3/4) |
| `position` | `PositiveIntegerField` | `default=0` | Ordering; `UniqueConstraint(checklist, position)` |
| `created_at` / `updated_at` | `DateTimeField` | auto | Key Entities |

**Meta**: `ordering = ["position", "id"]`; `UniqueConstraint(fields=["checklist","position"], name="uniq_item_position")`.

**State transitions**:

```text
active item ──toggle──▶ complete item
   ▲                        │
   └──────── toggle ◀───────┘
```
Creation appends at `max(position)+1`; editing changes `text`; deletion removes the
row (subsequent positions unchanged — renumbering is cosmetic, not required).

### 3. ChecklistShare — `checklists.models.ChecklistShare`

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `checklist` | `ForeignKey(Checklist)` | `on_delete=CASCADE`, `related_name="shares"` | Deleted-with-checklist (R12) |
| `recipient` | `ForeignKey(User)` | `on_delete=CASCADE`, `related_name="shared_checklists"` | FR-005 share with registered user |
| `shared_at` | `DateTimeField` | `auto_now_add` | Key Entities |
| `status` | `CharField` | choices {`active`,`revoked`}, default `active` | FR-008 revoke; history-preserving (R4) |

**Meta**: `UniqueConstraint(fields=["checklist","recipient"], name="uniq_share")`;
`ordering = ["-shared_at"]`.

**State transitions**:

```text
active ──revoke (FR-008)──▶ revoked      (row retained; reshare = active again)
```
Read-only contract for recipients (FR-007): no share ever grants edit — authorization
always requires `owner` (R4).

### 4. EmergencyContact — `checklists.models.EmergencyContact`

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `owner` | `ForeignKey(User)` | `on_delete=CASCADE`, `related_name="emergency_contacts"` | FR-009 designations |
| `contact` | `ForeignKey(User)` | `on_delete=CASCADE`, `related_name="owner_emergency_contacts"` | The designated contact |
| `designated_at` | `DateTimeField` | `auto_now_add` | Key Entities |

**Uniqueness**: `UniqueConstraint(fields=["owner","contact"], name="uniq_emergency_contact")`.
**Validation** (form + model `clean`): `owner != contact` (R5). Multiple contacts per
owner allowed (Assumption).

**State transition**: `active designation ──remove (acceptance 6)──▶ deleted`
(cascade: pending requests → `cancelled`, granted access revoked — R7, in a
transaction).

### 5. EmergencyAccessRequest — `checklists.models.EmergencyAccessRequest`

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `owner` | `ForeignKey(User)` | `on_delete=CASCADE`, `related_name="emergency_requests"` (owner side) | Target of access |
| `requester` | `ForeignKey(User)` | `on_delete=CASCADE`, `related_name="emergency_requests_made"` | The emergency contact requesting |
| `status` | `CharField` | choices {`pending`,`approved`,`denied`,`auto_granted`,`cancelled`}, default `pending` | R7 adds `cancelled` |
| `requested_at` | `DateTimeField` | `auto_now_add` | Key Entities |
| `resolved_at` | `DateTimeField` | `null=True`, blank | Set on final transition |
| `timeout_deadline` | `DateTimeField` | set at creation | `requested_at + settings.CLA_OK_EMERGENCY_AUTO_GRANT_HOURS` (default 72 h) |

A request is only valid when `requester` is a designated emergency contact of `owner`
(validated at creation — FR-010).

**State transitions** (guarded single-step, R9):

```text
                        ┌──owner approves──▶ approved
pending ──owner denies──┼──▶ denied
         ──auto-grant───┼──▶ auto_granted      (lazy, at deadline — R8)
         ──contact removed──▶ cancelled        (R7)
approved/auto_granted ──contact removed──▶ cancelled   (revoke grant, R7)
```
Every transition is a conditional compare-and-set so a race yields exactly one final
state. `resolved_at` is stamped on the transition that commits. `approved`/
`auto_granted` = viewer access to **all** owner checklists (R6); `denied`/`cancelled` =
no access.

### 6. Notification — `checklists.models.Notification`

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `recipient` | `ForeignKey(User)` | `on_delete=CASCADE`, `related_name="notifications"` | FR-014 |
| `type` | `CharField` | choices {`share`,`revocation`,`emergency_request`,`emergency_response`} | FR-014 / Key Entities |
| `message` | `CharField` | `max_length=280` | Rendered content (FR-014 acceptance 1) |
| `is_read` | `BooleanField` | `default=False` | FR-014/015 |
| `created_at` | `DateTimeField` | `auto_now_add` | FR-014 timestamp |
| `related_checklist` | `ForeignKey(Checklist)` | `null=True, blank, on_delete=SET_NULL` | Navigation target (FR-014 a.3) |
| `related_share` | `ForeignKey(ChecklistShare)` | `null=True, blank, on_delete=SET_NULL` | Share/revocation context |
| `related_request` | `ForeignKey(EmergencyAccessRequest)` | `null=True, blank, on_delete=SET_NULL` | Emergency context |

**Meta**: `ordering = ["-created_at"]`. Unread count = `recipient.notifications.filter(is_read=False).count()` (FR-016 badge context processor).

**State transitions** (per-user):

```text
unread ──mark read (single / click)──▶ read
unread/read ──"clear all"──▶ (rows deleted for recipient)
unread ──"mark all as read"──▶ read (bulk update)
```

---

## Validation rules (mapped from requirements)

| Rule | Requirement | Enforcement point |
|---|---|---|
| Checklist title required, ≤ 140 chars | FR-002 | `ChecklistForm` + model `max_length` |
| Item text required, ≤ 200 chars | FR-003 | `ChecklistItemForm` + model `max_length` |
| Share recipient is a **registered** user | FR-006 | `ShareForm.clean_recipient` → `User.objects.filter(email__iexact=...)`; reject unknown email with error (acceptance 2) |
| Recipients are **read-only** | FR-007, SC-006 | Authorization in `services.can_edit` (requires owner) + UI hides edit/delete controls; direct edit POST rejected |
| Recipient cannot self-share share checklists they already have | edge case | `UniqueConstraint(checklist, recipient)` + friendly "already shared" message on re-add (status flip back to active) |
| Emergency contact is a registered user | FR-009 | `EmergencyContactForm` by email; user lookup required |
| Owner ≠ emergency contact | edge case (self-designation) | Form/model `clean` error (R5) |
| Requester is a designated contact of owner | FR-010 | `services.request_emergency_access` validates existing `EmergencyContact(owner, requester)` |
| Auto-grant at configured timeout (default 72 h) | FR-011, SC-003 | `timeout_deadline` + lazy compare-on-read (R8); settings-driven |
| Notification recipient is a real user | FR-014 | `services.notify(recipient,...)` uses `User` FK |
| Auth on every feature endpoint | FR-019 | `LoginRequiredMixin` on all `checklists`/`notifications` views |
| Users manage only their own checklists/contacts | FR-020, SC-006 | `services.can_view`/`can_edit` + `get_object_or_404` scoped by `request.user`; errors, not leakage |

All validation server-side; errors render inline (Django form machinery). All
state-changing POSTs CSRF-protected.

## Edge-case dispositions (from spec § Edge Cases)

| Edge case | Behavior |
|---|---|
| Share a checklist already shared with the same user | Re-activate an existing `revoked` row or show "already shared" message; unique constraint prevents duplicates |
| Concurrent edits by multiple users | Out of scope — sharing is read-only (no collaborative editing). Owner-edits are single-writer; items updated via guards, no lost-update concern beyond last-write-wins on same owner |
| Owner deletes a shared checklist | Cascade deletes items + shares; recipients notified of deletion (R12); item disappears from their shared list |
| Emergency request with multiple designated contacts | Any *one* designated contact can independently request; each request is per (owner, requester) |
| User designates themselves as emergency contact | Rejected with inline error (R5) |
| Notification overflow (1000+ unread) | No row cap (FR-018); list paginated; "clear all"/"mark all read" bulk-operate on the whole set (R11) |
| Owner's account deactivated with active shares/emergency | FKs reference `User`; access guard adds `is_active` check on owner/recipient/contact; no schema change (R12) |
| Network failure during share/approval | Atomic DB transactions — a failed POST leaves no partial state; retry is safe (idempotent creation guards) |
| Owner changes email | Relationships key on User FK, not email string, so they survive an email change (R12) |
| Auto-grant racing a manual approval in progress | Single-step guarded transitions (compare-and-set); exactly one final state (R9) |

---

## Entity relationship summary

```text
accounts.User (existing)
   └── owner ◀── Checklist ──▶ ChecklistItem  (1:N)
   │                    └──▶ ChecklistShare   (1:N; recipient=User)
   │                    └──▶ Notification.related_checklist (nullable)
   ├── owner ──▶ EmergencyContact ──▶ contact (a User)
   ├── owner/requester ──▶ EmergencyAccessRequest
   └── recipient ──▶ Notification (1:N)
```
