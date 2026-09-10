# DFT-9 Web Contracts — Routes & Forms (Checklists, Sharing, Emergency Access, Notifications)

**Source**: `/specs/DFT-9/spec.md` FR-001…FR-020; see also
[`/specs/DFT-9/data-model.md`](../data-model.md) for the entities these contracts
read/write and [`/specs/DFT-9/research.md`](../research.md) for the design decisions
(R1 app split, R4 read-only sharing, R6/R8/R9 emergency semantics, R10 notifications).

Interface type: **server-rendered HTML web application** (no JSON API, no CLI). This
contract is the full externally visible surface added by DFT-9: URL routes, allowed
methods, authentication/authorization gates, redirect behavior, and form field
contracts. All state-changing requests (POST) are CSRF-protected (FR-011); a
missing/tampered token yields **HTTP 403** before the view runs. These routes are
mounted under the existing `config/urls.py` via `path("", include("checklists.urls"))`.

## Settings contract (holds from DFT-7; additions for DFT-9)

| Setting | Value |
|---|---|
| `AUTH_USER_MODEL` | `accounts.User` |
| `LOGIN_URL` | `/accounts/login/` |
| `LOGIN_REDIRECT_URL` | `/dashboard/` |
| `LOGOUT_REDIRECT_URL` | `/accounts/login/` |
| `ALLOWED_HOSTS` | `["localhost", "127.0.0.1", "testserver"]` (dev) |
| `CLA_OK_EMERGENCY_AUTO_GRANT_HOURS` (new) | integer, default `72` — auto-grant window (FR-011). Not user-facing. |
| `CLA_OK_TEMPLATES` (new) | code-defined quick-start set, e.g. `{"Grocery List": [...], "Travel Packing": [...], "Meeting Agenda": [...]}` (FR-017) |

`INSTALLED_APPS` gains `"checklists"` (after `accounts`); a `"checklists.context_processors.unread_notifications"`
entry is added to `TEMPLATES` OPTIONS for the header badge (FR-016).

## Authorization model (shared by all protected routes)

Two helpers in `checklists/services.py` gate every resource view:

- `can_edit(user, checklist)` → `True` only if `checklist.owner == user`.
- `can_view(user, checklist)` → `True` if `owner == user`, or there is an **active**
  `ChecklistShare` to `user`, or the user holds an `approved`/`auto_granted`
  emergency request against the owner.

Views fetch the resource with `get_object_or_404` scoped by the user's permitted set,
so a user who cannot view a checklist experiences the equivalent of **404 / error, not
data leakage** (SC-006, FR-020). Edit/delete actions additionally require `can_edit`;
shared/emergency viewers get read-only rendering.

## Routes

### Checklists (personal — owner manages)

**`GET /checklists/`** — personal checklist list (FR-001, sidebar nav "Checklists").
- Auth: required — unauthenticated → **302** `/accounts/login/?next=/checklists/`.
- Renders the user's owned checklists with title, item count, completion %, and a
  "New Checklist" action (SC-008).

**`GET /checklists/new/`** — create form (FR-002, FR-017). Renders title field +
template picker (quick-start pre-fill; FR-017 acceptance 1 shows titles + item counts).
**`POST /checklists/new/`** — create checklist (optionally from a template).
- Auth: required.
- Fields: `title` (required, ≤ 140), `template` (optional — on submit, pre-fills items
  from the chosen `CLA_OK_TEMPLATES` entry; FR-017 acceptance 2).
- Success: **302** → `/checklists/<id>/`.
- Failure (blank title / unknown template): re-render **200** with inline errors.

**`GET /checklists/<id>/`** — checklist detail (FR-001/003/004).
- Auth: required. AuthZ: **view** (`can_view`). If the user is a *recipient*
  (share or emergency) the page renders read-only: completion stats shown, add/edit/
  delete controls omitted, "Shared by [owner]" label shown (acceptance 3); direct edit
  POSTs are rejected at the view guard (FR-007, SC-006).

**`POST /checklists/<id>/items/`** — add item (FR-003 acceptance 2). Field `text`
(required, ≤ 200). AuthZ: **edit**. Success: **302** → `/checklists/<id>/`.

**`POST /checklists/<id>/items/<item_id>/toggle/`** — toggle `is_complete` (FR-003
acceptance 3/4). AuthZ: **edit**. Success: **302** back; stats recompute.

**`POST /checklists/<id>/items/<item_id>/edit/`** — edit item text (acceptance 5).
Field `text`. AuthZ: **edit**. Success: **302** back.

**`POST /checklists/<id>/items/<item_id>/delete/`** — delete item (acceptance 6). AuthZ:
**edit**. Success: **302** back (count recomputed).

**`GET /checklists/<id>/delete/`** — confirm delete (FR-003 acceptance 7).
**`POST /checklists/<id>/delete/`** — delete the checklist (cascades items + shares;
recipients notified — R12). AuthZ: **edit**. Success: **302** → `/checklists/`.

### Sharing (owner)

**`GET /checklists/<id>/share/`** — share page: share-with form + list of current
recipients with revoke actions (FR-005/008).
**`POST /checklists/<id>/share/`** — share with a registered email.
- Auth: required. AuthZ: **edit** (owner only).
- Field `email` (recipient). Validation (FR-006):
  - Unknown/unregistered email → re-render **200** with error "No user with that email
    address." (acceptance 2). Nothing created.
  - Self-share → error (edge case).
  - Already an active recipient → message "Already shared with this user." (no-op /
    reactivate).
  - Success: create `ChecklistShare(active)`, send **share** notification to recipient
    (FR-005 acceptance 1), **302** → `/checklists/<id>/share/`.

**`POST /checklists/<id>/share/<share_id>/revoke/`** — revoke sharing (FR-008).
- Auth: required. AuthZ: **edit**.
- Sets share `status = "revoked"`; sends **revocation** notification to the recipient
  (acceptance 6). Success: **302** → `/checklists/<id>/share/`. Recipient loses the
  checklist from their shared list (acceptance 5).

### Shared checklists (recipient)

**`GET /checklists/shared/`** — lists checklists shared *with* the user (FR-005
acceptance 3) — active shares + emergency grants, each labelled "Shared by [owner]".
Renders them read-only. Auth: required.

### Emergency access (owner & contact)

**`GET /emergency/`** — owner's emergency contact management (FR-009 acceptance 1):
list designated contacts + a designate form.
**`POST /emergency/`** — designate an emergency contact by email.
- Auth: required. AuthZ: owner (self).
- Field `email` (the contact). Validation:
  - Unregistered email → inline "No user with that email address."
  - Self-designation (`owner == contact`) → inline "Cannot designate yourself." (R5).
  - Duplicate → "Already an emergency contact."
  - Success: create `EmergencyContact`; **302** → `/emergency/` (contact appears, accept. 1).

**`POST /emergency/<contact_id>/remove/`** — remove an emergency contact (acceptance 6).
- Auth: required. AuthZ: owner.
- In one transaction: mark pending requests `cancelled`, revoke granted access
  (approved/auto_granted → `cancelled`, R7), delete the relationship; notify the
  removed contact if they held access. **302** → `/emergency/`.

**`GET /emergency/request/`** — contact's emergency-access page: shows the request
state for each owner they are a designated contact of, with a "Request access" action.
Auth: required (the *contact*).

**`POST /emergency/request/<owner_id>/`** — request emergency access (FR-010).
- Valid only if the caller is a designated `EmergencyContact` of `owner` (R8/R9 guard).
- If no unresolved request exists, create `pending` with `timeout_deadline =
  now + CLA_OK_EMERGENCY_AUTO_GRANT_HOURS`; notify the **owner** of the request
  (FR-012, acceptance 2). If an `auto_granted` deadline has passed, resolve to
  `auto_granted` first, then grant.
- Success: **302** → `/emergency/request/` (or straight to granted view if already
  auto-granted).
- This route does **not** immediately grant — it either (re)states a pending request
  or resolves an already-expired one to auto-grant (lazy, R8).

**`GET /emergency/request/<request_id>/respond/`** — owner's response page (approve/
deny). Auth: required; **owner of the request only**.
**`POST /emergency/request/<request_id>/approve/`** — approve (FR-013; acceptance 3).
- Guarded `pending → approved` (R9). If already resolved → redirect back with a
  "request already resolved" message (no double-apply). On success: attach viewer
  access (all owner checklists), notify **both** owner + contact.
**`POST /emergency/request/<request_id>/deny/`** — deny (acceptance 4). Guarded
`pending → denied`; notify contact of denial; no access. Idempotent no-op if resolved.

### Notifications

**`GET /notifications/`** — notification center (FR-014 acceptance 1/2): paginated
list (newest first), each with message, timestamp, unread indicator; click navigates to
the related context (related_checklist/share/request) and marks the notification read
(acceptance 3).
Auth: required.

**`POST /notifications/<id>/read/`** — mark one read (FR-015; acceptance 3).
**`POST /notifications/read-all/`** — mark all read (acceptance 4). Bulk update.
**`POST /notifications/clear/`** — clear all (acceptance 5). Bulk delete for the user.

**Header badge (FR-016)** — the dashboard/base header renders the unread count from
the `unread_notifications` context processor (SC-007). It is read-only markup, no route.

## HTTP status summary

| Route | Method | Auth | AuthZ | Success | Errors |
|---|---|---|---|---|---|
| `/checklists/` | GET | req | — | 200 list | 302 → login |
| `/checklists/new/` | GET/POST | req | — | 302 → detail / 200 form | 302 → login; 200 + inline |
| `/checklists/<id>/` | GET | req | **view** | 200 (+ read-only if recipient) | 302 → login; 404/error if no view |
| `/checklists/<id>/items/` | POST | req | **edit** | 302 → detail | 302 → login; 404/403 if no edit; 200 + inline |
| `/checklists/<id>/items/<i>/toggle/` `edit/` `delete/` | POST | req | **edit** | 302 → detail | 302 → login; 404/403 |
| `/checklists/<id>/delete/` | GET/POST | req | **edit** | 302 → list | 302 → login; 404/403 |
| `/checklists/<id>/share/` | GET/POST | req | **edit** | 302 → share | 302 → login; 404/403; 200 + inline |
| `/checklists/<id>/share/<s>/revoke/` | POST | req | **edit** | 302 → share | 302 → login; 404/403 |
| `/checklists/shared/` | GET | req | — | 200 list | 302 → login |
| `/emergency/` | GET/POST | req | owner(self) | 302 → emergency | 302 → login; 200 + inline |
| `/emergency/<c>/remove/` | POST | req | owner | 302 → emergency | 302 → login; 404/403 |
| `/emergency/request/` | GET | req | contact | 200 | 302 → login |
| `/emergency/request/<o>/` | POST | req | designated contact | 302 → request | 302 → login; 403 if not contact |
| `/emergency/request/<r>/respond/` | GET | req | request owner | 200 | 302 → login; 404/403 |
| `/emergency/request/<r>/approve/` `deny/` | POST | req | request owner | 302 → respond/request | 302 → login; 404/403; no-op if resolved |
| `/notifications/` | GET | req | — | 200 | 302 → login |
| `/notifications/<id>/read/` `read-all/` `clear/` | POST | req | — | 302 → `/notifications/` | 302 → login |
| any POST with bad/missing CSRF | — | — | — | — | **403** |

## Template surface (SC-008)

- `templates/base.html` — **edited**: sidebar gains "Checklists" (`/checklists/`) and
  "Notifications" (`/notifications/`) links; header gains the unread badge (FR-016).
- `templates/checklists/` — **new**:
  - `checklist_list.html`, `checklist_shared_list.html`
  - `checklist_detail.html` (renders read-only when recipient/emergency)
  - `checklist_form.html` (title + template picker), `checklist_confirm_delete.html`
  - `share_form.html` (share + revoke), `emergency_contacts.html`
  - `notification_list.html` (center: read/unread, clear all)
- Existing `dashboard/`, `accounts/`, `registration/` templates unchanged (only
  `base.html` shell is edited).

## Non-contract surface (explicitly out of scope)

- No JSON/REST API, no schema/OpenAPI.
- No email/SMS/push notifications (in-app only, FR-014 Assumption).
- No collaborative editing (recipients read-only).
- No admin UI for templates (code-defined `CLA_OK_TEMPLATES`), no user-facing timeout
  setting (settings-only `CLA_OK_EMERGENCY_AUTO_GRANT_HOURS`).
- `/admin/` remains Django's stock admin (dev convenience; new models may be
  registered for inspection only).
- No change-email UI; deactivation/account lifecycle out of scope (data-layer guards only).
