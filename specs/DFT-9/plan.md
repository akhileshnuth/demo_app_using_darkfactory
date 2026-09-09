# Implementation Plan: Checklists, Secure Sharing, Emergency Access & Notifications

**Branch**: `DFT-9-checklists-sharing-emergency` | **Date**: 2026-09-09 | **Spec**: [`/specs/DFT-9/spec.md`](spec.md)

**Input**: Feature specification from `/specs/DFT-9/spec.md` — Approved spec ("Checklists, secure sharing, emergency access & notifications").

## Summary

Extend the DFT-7/DFT-8 Django application with a first-party `checklists` app that
delivers four integrated capabilities on top of the existing `accounts` user model
and `dashboard` shell:

1. **Personal checklists** (P1) — create titled checklists, add/edit/delete/toggle
   items, completion statistics, full persistence (SQLite via Django ORM). Accessible
   from the dashboard sidebar.
2. **Secure sharing** (P2) — owners share a checklist with registered users by email;
   recipients get read-only view, owners can revoke; notifications on both sides.
3. **Emergency access** (P3) — designated emergency contacts can request access to all
   of an owner's checklists; owner approves/denies; auto-grant after a configurable
   timeout (default 72 h) ; removal revokes pending + granted access.
4. **Notifications** (P2) — in-app notification center with unread indicators,
   mark-read/clear-all, and an unread badge in the dashboard header; plus **checklist
   templates** (P3) for quick-start creation.

All four features are server-rendered Django (no JS framework), reuse the email-keyed
`accounts.User`, SQLite storage, Django's bundled test runner, and add **no** novel
runtime dependencies. Emergency access grants are viewer-scope only (read-only), the
72 h timeout is a settings-driven system constant (not user-visible), and templates
are a code-defined static set.

## Technical Context

**Language/Version**: Python 3.11+ (Django 5.2 LTS). Pinned `Django~=5.2` in
`requirements.txt` (DFT-7 established). Runtime is the factory sandbox (Node-only —
`overlays/python/README.md`), so Python must be installed locally by the
implementer/human reviewer; dependency install and test runs are NOT executed by the
factory pipeline (ticket ships **UNVERIFIED**, see Constitution Check).

**Primary Dependencies**: Django 5.2 LTS with built-ins: `django.contrib.auth`
(login/session for `LoginRequiredMixin` and `request.user`), `django.contrib.messages`
(optional subset of notifications), `django.contrib.staticfiles`, `django.contrib.admin`
(dev convenience). **No third-party runtime packages** — no DRF, no celery, no
background-task queue, no external notification service. The 72 h emergency-timeout
"job" is a lazy check evaluated on access requests (a poll-on-read), not a scheduled
daemon, so no async infra is introduced.

**Storage**: SQLite (Django default) for dev/test (`settings.DATABASES`). Data
model: four new entities in a new `checklists` app (`Checklist`, `ChecklistItem`,
`ChecklistShare`, `EmergencyContact`, `EmergencyAccessRequest`) plus a `Notification`
entity. Production DB out of scope.

**Testing**: Django's bundled runner (`python manage.py test` / `python -m django test`)
with the in-memory test DB — zero external services. As in DFT-7/DFT-8, the factory
sandbox cannot run Python tests; the implementer's local run is the SC-005/SC-006
authority and the ticket is marked **UNVERIFIED** for the human approver.

**Target Platform**: Linux server; runnable locally. Server-rendered Django
templates, desktop-first layout (side nav + main area), consistent with the existing
`base.html` / `dashboard.html` shell.

**Project Type**: web-service (server-rendered Django application). No JSON/REST
API, no CLI.

**Performance Goals**: UX-scale, not load-scale (SC-001–SC-004): create a 5-item
checklist in < 30 s; share + recipient-visible in < 10 s; auto-grant exactly at the
configured timeout; notification visible within 5 s. No throughput targets.

**Constraints**: Read-only sharing (no collaborative editing — out of scope).
Emergency access is all-or-nothing across an owner's checklists (no per-checklist
granularity in v1). In-app notifications only (no email/SMS/push). Templates are a
code-defined set (no admin editor). 72 h timeout is a system setting, not user-facing.
Mode output is server-rendered HTML; all state-changing POSTs are CSRF-protected.
Configuration lives in `config/settings.py`; the new feature's app-registration and
URL wiring live in `config/urls.py`.

**Scale/Scope**: One new first-party Django app (`checklists/`) covering models,
views, forms, URLs, and templates, plus template extensions to the shared shell's
sidebar/header and an unread-badge context processor. 5 new entities + 1 new view
family + notification center. Reuses `accounts.User`, `dashboard` shell, `base.html`.
`accounts/` (auth/PII surface) is **not** modified by this ticket — this keeps the
impact inside a single new app and off the zoned auth/PII paths (see Constitution
Check + Complexity Tracking).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Reviewed against `constitution.md`.

- **Principle I — Spec-Kit completeness**: Full pipeline in progress (Spec → Plan →
  Tasks → Implement → Converge). This ticket continues the pipeline; a prior DFT-9
  attempt stopped at implement (no source shipped). **PASS**.
- **Principle II — Security zones declared**: `SECURITY_ZONES.md` still carries the
  template-default rows (`src/auth:auth`, `src/payments:payments`, `src/customers:pii`)
  that name paths this repo does not have (this was already flagged in DFT-7 research
  R12). This ticket adds **sharing, emergency access, and notifications** — all of
  which write additional personal data (who shares with whom, who is someone's
  emergency contact, notification content) and so extend the `pii`-sensitive surface.
  **GATE VIOLATION (unjustified today)**: the zone map is stale. Resolution: the plan
  records the real sensitive paths (existing `accounts/` auth/PII + the new
  `checklists/` sharing/emergency surface) and instructs the implementer to update
  `SECURITY_ZONES.md` and the factory zone map (`agentguard/policies/zones/zones-v0.json`
  or `FACTORY_ZONES`) **before** writing the new checklists code. Because the factory
  enforces from its own config (still `src/...`), no row currently matches; once
  mapped, agent writes into zoned paths are denied and those files become human work
  — the implementer must reconcile the PR plan accordingly. See Complexity Tracking.
- **Principle III — Human-gated merge**: Changes land via PR to protected `main` with
  human review + CI. **PASS** (enforced at repo/factory level).
- **Principle IV — Test-first**: Functional changes require tests. Standard Django
  test runner is self-contained. Tests are planned for checklist CRUD, sharing +
  read-only enforcement, emergency access flow + auto-grant, notification center,
  and authorization failures. **PASS**, with the Python-overlay caveat (below).
- **Principle V — No novel dependencies**: No runtime deps beyond Django itself.
  **PASS**. Autonomy-eligible.
- **Security/Verification (python overlay)**: `overlays/python/README.md` states the
  factory sandbox has no Python, no PyPI egress, and cannot run Python tests — such
  tickets are marked **UNVERIFIED**. The implementer must run `python manage.py test`
  locally and the human approver must verify SC-005/SC-006/SC-007 from that local run.
  Recorded as an accepted, known constraint.

**Gate result (pre-research)**: **PASS with one required condition** — the stale
`SECURITY_ZONES.md` / factory zone-map (Principle II) must be resolved before the new
`checklists/` code is written. All other gates pass.

**Gate result (post-design, re-check)**: Still **PASS with the same single condition**,
now concretely scoped (see research R13 / data-model). Phase 0/1 resolved every
`NEEDS CLARIFICATION`; the zone gap is a named implementation step, not an unknown:
- R13 (`research.md`) maps the newly-affected sensitive surfaces: the new
  `checklists/` sharing/emergency/notification data → `pii` (and the pre-existing
  `accounts/` auth/PII already mapped in DFT-7 R12). The factory's config must be
  updated before the implementer writes the checklists code.
- All other principles re-confirmed post-design: I (full pipeline in flight), III (PR +
  human merge), IV (tests planned via Django's bundled runner; local run is the
  SC-005/006/007 authority), V (no novel runtime dependencies).
- The 72 h auto-grant is implemented as a **lazy, poll-on-read** check (evaluated
  when a pending request is inspected / when the contact requests access), not a
  background daemon — avoiding async infra and keeping Principle V clean. Detailed in
  research R11 and quickstart.

## Project Structure

### Documentation (this feature)

```text
specs/DFT-9/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── web-contracts.md # Server-rendered routes + forms for checklists/sharing/emergency/notifications
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

The feature lands in one new first-party app `checklists/` at the repo root, matching
the flat Django layout established by DFT-7 (`accounts/`, `dashboard/`, `templates/`,
`manage.py`). The shared shell (`templates/base.html`, `dashboard/`) is touched only
to add the checklist nav links, the notifications badge, and an unread-count context
processor. `accounts/` is intentionally **not** modified (keeps the zoned auth/PII
surface clear; sharing/notification build on the existing `User`).

```text
manage.py                     # existing
requirements.txt              # unchanged — Django~=5.2 only (no novel deps)
config/
├── settings.py               # (+ add "checklists" to INSTALLED_APPS;
│                             #   + CLA_OK_EMERGENCY_AUTO_GRANT_HOURS (default 72)
│                             #   + CLA_OK_TEMPLATES (code-defined quick-start set);
│                             #   + context-processor for unread-notification badge)
└── urls.py                   # (+ include("checklists.urls"))
accounts/                     # existing — NOT modified by this ticket (zoned auth/PII)
dashboard/                    # existing — shell view unchanged
templates/
├── base.html                 # (+ sidebar nav: Checklists, Notifications;
│                             #   + header unread-notification badge; read-only share label hook)
└── checklists/               # NEW: app templates
    ├── checklist_list.html           # user's personal checklists
    ├── checklist_shared_list.html    # shares received by this user
    ├── checklist_detail.html         # items + completion stats; read-only if shared/emergency
    ├── checklist_form.html           # create/edit title (with template picker)
    ├── checklist_confirm_delete.html # delete checklist
    ├── share_form.html              # share with a registered email; list + revoke
    ├── emergency_contacts.html      # designate/remove emergency contacts
    └── notification_list.html       # notification center (read/unread, clear all)
checklists/                          # NEW: first-party app
├── __init__.py
├── apps.py
├── models.py                 # Checklist, ChecklistItem, ChecklistShare,
│                             #   EmergencyContact, EmergencyAccessRequest, Notification
├── services.py               # policy logic: can_view/can_edit, auto-grant eval,
│                             #   revoke cascades, notification creation + unread counts
├── views.py                  # class-based views (LoginRequired) for each surface
├── forms.py                  # ChecklistForm, ChecklistItemForm, ShareForm,
│                             #   EmergencyContactForm
├── urls.py                   # /checklists/... , /notifications/...
├── admin.py                  # dev convenience registrations
├── context_processors.py     # unread notification count for header badge
├── migrations/
└── tests.py                  # SC-005/006/007: checklist CRUD + stats, share +
                              #   read-only enforcement + revoke, emergency flow +
                              #   auto-grant, notification center, authorization
```

**Structure Decision**: Chosen the flat Django web-service layout (as in DFT-7 —
"Option 2: web application", adapted; no `backend/`+`frontend/` split because there is
no separate JS frontend — Django templates are the UI). The feature is isolated in a
single first-party app `checklists/` so the zoned `accounts/` auth/PII surface stays
untouched and the impact is reviewable as one app. Complemented by small edits to
`templates/base.html` and a `context_processors.py` under `checklists/`. No new
runtime dependencies, so no intra-app package walls are needed.

## Complexity Tracking

> Filled because Constitution Check (Principle II) has a violation that must be justified.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Principle II zone mismatch (stale `SECURITY_ZONES.md`) | The factory's zone map still points at template-default `src/auth`, `src/payments`, `src/customers`, while this repo's real sensitive surfaces are `accounts/` (auth/PII, from DFT-7) plus the new `checklists/` sharing/emergency/notification data (PII). Before writing the new checklist/sharing/emergency/notification code, the map must name these real paths so Principle II enforcement reflects the actual repo. | Restructuring the whole Django app under a `src/` hierarchy to match the current template rows — rejected (empty structure churn; diverges from the established DFT-7/DFT-8 flat layout; leaves the genuine `accounts/`+`checklists/` surfaces still unmapped). Updating `SECURITY_ZONES.md` + the factory zone map to the real Django paths is the minimal, correct fix. |

## Phase 0-1 Output

Phase 0 research and Phase 1 design artifacts are generated and stored as:
- `./specs/DFT-9/research.md`
- `./specs/DFT-9/data-model.md`
- `./specs/DFT-9/contracts/web-contracts.md`
- `./specs/DFT-9/quickstart.md`
