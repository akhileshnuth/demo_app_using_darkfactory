# DFT-9 Quickstart — Validation Guide

**Purpose**: Prove the checklists/sharing/emergency/notifications feature works
end-to-end. This is a run/validate guide.
**References**: Route/form contracts [`contracts/web-contracts.md`](contracts/web-contracts.md);
entities & validation [`data-model.md`](data-model.md); decisions
[`research.md`](research.md).

> **Factory note**: this repo's Python overlay is not yet supported by the factory
> sandbox (`overlays/python/README.md`) — the CI pipeline cannot install Python or run
> the test suite, and this ticket ships **UNVERIFIED**. The commands below are the
> authority for SC-005/006/007 and must be run by the implementer locally; the human
> approver checks SC-005/006/007 against this run.

## Prerequisites

- Python 3.11+ on the machine running validation.
- Git branch `DFT-9-checklists-sharing-emergency` checked out.
- Existing DFT-7/DFT-8 scaffold present (`manage.py`, `config/`, `accounts/`,
  `dashboard/`, `templates/`).
- **Before implementing**, update `SECURITY_ZONES.md` and the factory zone map to the
  real Django paths named in [`research.md`](research.md) R13 (Constitution Principle
  II precondition).
- From repo root: `python -m venv .venv && source .venv/bin/activate`
- `pip install -r requirements.txt` (installs `Django~=5.2` only — no novel deps).

## Setup

```bash
python manage.py makemigrations checklists     # creates the 6 new-checklists tables
python manage.py migrate                       # SQLite dev DB (db.sqlite3)
```

No seed data required — flows create their own users. Two registered users are needed
for sharing/emergency tests (e.g. `owner@example.com` and `contact@example.com`, both
created via `/accounts/signup/` or the test client / `createsuperuser`).

## Validation scenarios (map to Success Criteria)

### 1. App wiring & settings — SC-008

```bash
python manage.py check
python manage.py runserver 0.0.0.0:8000
```

Expected: `"checklists"` in `INSTALLED_APPS`; `CLA_OK_EMERGENCY_AUTO_GRANT_HOURS=72`
default present (FR-011); `CLA_OK_TEMPLATES` defined (FR-017); sidebar shows
"Checklists" and "Notifications" links and the header shows the unread badge (FR-016).
Logged-in navigation to `/checklists/`, `/checklists/shared/`, `/emergency/`,
`/emergency/request/`, `/notifications/` all render their shells.

### 2. Full test suite — SC-005/006/007

```bash
python manage.py test            # Django's built-in runner, in-memory SQLite
```

Expected: **zero failures** covering checklist CRUD + completion stats (SC-001),
sharing + read-only enforcement + revoke (SC-002/006), emergency request/approve/deny/
auto-grant/revoke (SC-003), notification center + unread badge/read-state (SC-004/007),
and authorization (SC-006 — no leakage).

### 3. Personal checklist lifecycle — SC-001, FR-001…004

Logged in as `owner@example.com`: `GET /checklists/new/` → title "Grocery Run" →
Create. Add 5 items (milk, eggs, bread, coffee, butter), each `POST
/checklists/<id>/items/`. Toggle a couple complete.

Expected: list shows item count + completion % (FR-004); toggling a complete item
styling/strikethrough applies and % updates immediately (acceptance 3/4); edit one
item's text, delete one item → count decrements (acceptance 5/6); reload the page → all
changes persist (SC-001 create 5-item checklist in < 30 s; SC-005 no data loss).

Template check (FR-017): at `new/` browse the template list (titles + item counts,
acceptance 1); pick "Travel Packing" → a checklist with its pre-filled items is created
(acceptance 2); edit/delete a pre-filled item normally (acceptance 3).

### 4. Sharing + read-only + revoke — SC-002/006, FR-005…008

Logged in as `owner@example.com` on `/checklists/<id>/share/`, share with
`contact@example.com` (a registered user).

Expected: share created; recipient gets a **share** notification (SC-004, FR-014);
logged in as `contact@example.com`, `/checklists/shared/` shows the checklist labelled
"Shared by owner@example.com" (acceptance 3, SC-002 within 10 s); clicking into it the
items are visible **read-only** — no add/edit/delete controls, and a direct `POST
/checklists/<id>/items/` from the recipient is rejected (SC-006, FR-007).

Negative: share with `nobody@example.com` (unregistered) → inline "No user with that
email address.", nothing created (FR-006 acceptance 2). Share again with the same
recipient → "Already shared" message (edge case).

Revoke: owner `POST /checklists/<id>/share/<s>/revoke/`. Expected: recipient loses it
from `/checklists/shared/` (acceptance 5) and receives a **revocation** notification
(acceptance 6).

### 5. Emergency access flow — SC-003, FR-009…013

Logged in as `owner@example.com`, `GET /emergency/` → designate `contact@example.com`
(fr-009 acceptance 1). Try designating yourself → inline error (edge case).

As `contact@example.com`: `GET /emergency/request/` → `POST /emergency/request/<owner_id>/`.
Expected: owner gets an immediate **emergency_request** notification (FR-012,
acceptance 2). Owner approves: `POST /emergency/request/<r>/approve/`. Expected: both
parties notified (FR-013); `contact` gains read-only viewer access to **all** of
owner's checklists (acceptance 3, SC-006 read-only).

Auto-grant (FR-011, SC-003): set `CLA_OK_EMERGENCY_AUTO_GRANT_HOURS=0` locally (or wait
out the window), create a new pending request and revisit `contact`'s request page —
the request transitions to `auto_granted` with **no manual action** and both parties
are notified. (The lazy, poll-on-read design means the trigger is the next read after
the deadline — see research R8.)

Deny path: another request → owner denies → contact notified of denial, no access
(acceptance 4). Remove the emergency contact: pending requests cancelled and any granted
access revoked, both in one transaction (acceptance 6).

### 6. Notification center — SC-004/007, FR-014/015/016

After triggering several events (share, revocation, emergency request/response),
`GET /notifications/` shows them newest-first with message + timestamp + unread
indicator (FR-014 acceptance 1/2). Click one → marked read and navigates to the related
context (acceptance 3). Use "mark all read" → unread count clears (acceptance 4). Use
"clear all" → list empties (acceptance 5). The header badge count matches the unread
count and updates on read/clear (FR-016, SC-007).

### 7. Access control & authorization — FR-019/020, SC-006

From an anonymous browser: `GET /checklists/`, `/checklists/shared/`, `/emergency/`,
`/notifications/` all **302 → `/accounts/login/?next=<page>`** with no content in the
redirect (SC-003-style).

As a user who neither owns nor has been shared a checklist: `GET /checklists/<id>/`
and edit/delete POSTs → **404/403**, not leakage (SC-006). Cross-account verify: a
`contact` who is not an owner cannot manage the owner's checklists (FR-020).

### 8. CSRF — FR-011

Any POST without a CSRF token (e.g. `curl -X POST http://localhost:8000/checklists/new/`)
→ **403** with no state change. All new forms include `{% csrf_token %}`.

## Edge-case spot checks (from spec § Edge Cases)

| Check | Expected |
|---|---|
| Share with an already-shared recipient | "Already shared" message / reactivation; no duplicate rows (unique constraint) |
| Delete a shared checklist | Items + shares cascade; recipient notified; item vanishes from their shared list |
| Designate self as emergency contact | Inline error; nothing created |
| 1000+ unread notifications | Center paginates; "clear all"/"mark all read" act on the whole set; badge shows raw count |
| Auto-grant racing a manual approval/denial | Guarded single-step; exactly one final state, no contradictory notifications |
| Any POST with tampered CSRF | 403, no state change |

## What "done" looks like (checklist)

- [ ] `manage.py check` — 0 issues
- [ ] `manage.py test` — zero failures (SC-005/006/007)
- [ ] Create a 5-item checklist in < 30 s; stats update; persistence on reload (SC-001, SC-005)
- [ ] Template quick-start creates + persists pre-filled items (FR-017)
- [ ] Share to registered email → recipient notified + sees read-only "Shared by" list
      < 10 s (SC-002, SC-004); unregistered email rejected (FR-006)
- [ ] Recipient cannot edit/delete; direct edit POST rejected (SC-006, FR-007)
- [ ] Revoke → recipient loses access + gets revocation notification (FR-008)
- [ ] Emergency designate/request/approve/deny/auto-grant/revoke all behave per contract
      (FR-009…013, SC-003); auto-grant at timeout with zero manual intervention
- [ ] Notification center: read/unread, mark-one/all-read, clear-all, header badge
      (FR-014/015/016, SC-004/007)
- [ ] Anonymous + unauthorized access redirects/404s with no leakage (FR-019/020, SC-006)
- [ ] CSRF rejection observed (FR-011)
- [ ] `SECURITY_ZONES.md` + factory zone map updated to real paths (Principle II precondition)
