# DFT-8 Quickstart — Validation Guide

**Purpose**: Prove the document vault works end-to-end. This is a run/validate
guide — implementation details live in the plan and tasks.
**References**: Route/form contracts [`contracts/web-contracts.md`](contracts/web-contracts.md);
entities & validation [`data-model.md`](data-model.md); decisions
[`research.md`](research.md).

> **Factory note**: this repo's Python overlay is not yet supported by the factory
> sandbox (`overlays/python/README.md`) — the CI pipeline cannot install Python or
> run the test suite, and this ticket ships **UNVERIFIED**. The commands below are
> the authority for SC-005 and must be run by the implementer locally; the human
> approver checks SC-005 against this run.

## Prerequisites

- Python 3.11+ on the machine running validation
- Git branch `DFT-8-document-vault-core` checked out (based on DFT-7)
- From repo root: `python -m venv .venv && source .venv/bin/activate`
- `pip install -r requirements.txt` (installs `Django~=5.2`)

## Setup

```bash
python manage.py makemigrations vault    # creates vault migrations (Category, Subject, DocumentType, Document)
python manage.py migrate                 # SQLite dev DB (db.sqlite3) — includes DFT-7 accounts migrations
```

No seed data required — the flows create their own users and vault entities.

## Validation scenarios (mapped to Success Criteria)

### 1. System check passes — SC-004, FR-016, FR-017

```bash
python manage.py check
```

Expected: zero issues. The `vault` app is registered in `INSTALLED_APPS`
(FR-016) and its URL patterns are included in root `config/urls.py` (FR-017).

### 2. Full test suite — SC-005

```bash
python manage.py test vault -v2
```

Expected: **zero failures** across vault tests covering:
- **Models**: field constraints, `unique=True`, `UniqueConstraint(owner, title)`,
  `on_delete=PROTECT` on taxonomy FKs, `on_delete=CASCADE` on owner FK,
  `Meta.ordering`, `__str__` representations.
- **Views**: CRUD lifecycle for all 4 entities, `LoginRequiredMixin` enforcement
  (302 → login on unauthenticated GET), per-user document scoping (404 for
  other user's documents), taxonomy delete protection (blocked when documents
  reference), document list filtering, integrity error handling for duplicate
  titles/names.
- **Forms**: case-insensitive duplicate name rejection, required field validation,
  owner set automatically on document create.
- **URLs**: all 17 route names resolve to correct paths.

Also run the full suite to confirm no regressions:

```bash
python manage.py test -v2
```

Expected: zero failures across `accounts`, `dashboard`, and `vault`.

### 3. Full vault CRUD lifecycle — SC-001

Manual (or with the test client): register a user, then perform the complete
vault flow. Target: under 3 minutes from first vault navigation (SC-001).

**Step 1 — Create taxonomy entities:**
1. Navigate to `/vault/categories/` → "New Category" → name: "Financial",
   description: "Financial documents" → Save → redirected to list, "Financial" visible.
2. Navigate to `/vault/subjects/` → "New Subject" → name: "Tax Returns",
   description: "Annual tax filings" → Save → redirected to list, "Tax Returns" visible.
3. Navigate to `/vault/types/` → "New Document Type" → name: "Invoice",
   description: "Billing documents" → Save → redirected to list, "Invoice" visible.

**Step 2 — Create a document:**
4. Navigate to `/vault/` → "New Document" → title: "Q4 Invoice", category:
   "Financial", subject: "Tax Returns", type: "Invoice", notes: "Fourth quarter
   billing" → Save → redirected to list, "Q4 Invoice" visible.

**Step 3 — View document detail:**
5. Click "Q4 Invoice" in the list → detail page shows title, category, subject,
   type, notes, and timestamps (created/updated).

**Step 4 — Edit document:**
6. Click "Edit" on the detail page → change title to "Q4 Invoice - Updated" →
   Save → detail page shows updated title; list shows the document first (most
   recently updated).

**Step 5 — Delete document:**
7. Click "Delete" on the detail page → confirmation page shows document title →
   confirm → redirected to list, document no longer present.

### 4. Category/Subject/Type CRUD — FR-007, FR-008, FR-009

**Edit:**
1. On a taxonomy list page, click "Edit" next to an entity → change the name →
   Save → redirected to list, updated name visible.

**Delete (unreferenced):**
2. Create a category with no documents assigned → click "Delete" → confirm →
   redirected to list, category removed.

**Delete (referenced — blocked):**
3. Create a document assigned to a category → navigate to that category's delete
   page → confirm delete → page re-renders with inline error: "This category
   has 1 document(s) and cannot be deleted." Category is **not** removed (R1, R8).

### 5. Duplicate validation — SC-006

**Taxonomy duplicate name (FR-014):**
1. Create a category named "Financial" → try to create another category named
   "Financial" → inline error: "Category with this Name already exists."
2. Try to create a category named "financial" (different case) → inline error:
   "A category with this name already exists." (case-insensitive check, R6).

**Document duplicate title per user (FR-013):**
3. Create a document titled "My Report" → try to create another document titled
   "My Report" → inline error: "You already have a document with this title."
4. Try "my report" (different case) → same inline error (case-insensitive, R5).

**Cross-user title uniqueness:**
5. Register a second user → create a document titled "My Report" → succeeds
   (different owner; FR-013 is per-user).

### 6. Per-user document isolation — SC-002

1. Register two users (e.g., `alice@example.com` and `bob@example.com`).
2. As Alice: create 2 documents → verify both appear on `/vault/`.
3. Log out, log in as Bob: `/vault/` shows **zero documents** (SC-002).
4. Try to access Alice's document directly via URL (`/vault/documents/<alice_pk>/`):
   **404** — existence not leaked (R7).

### 7. Access control — SC-003, FR-011

From an anonymous browser:
- `GET /vault/` → **302** to `/accounts/login/?next=/vault/`
- `GET /vault/categories/` → **302** to `/accounts/login/?next=/vault/categories/`
- `GET /vault/documents/new/` → **302** to `/accounts/login/?next=/vault/documents/new/`

Expected: redirect responses contain **no vault content** (SC-003). Follow the
`?next=` after login and land back on the requested page.

Unauthenticated POST → **405** (Django 5.2 `LoginRequiredMixin` behavior; R12).

### 8. CSRF — FR-015

Any POST made without a CSRF token (e.g. `curl -X POST http://localhost:8000/vault/categories/new/`)
→ **403 Forbidden** with no authentication side effects. All UI forms include
`{% csrf_token %}`.

### 9. Document list filtering — User Story 6

1. Create 3 documents with different categories/subjects/types.
2. On `/vault/` select a category filter → only documents in that category shown.
3. Enter a search term in the title search → only matching documents shown.
4. Clear all filters (navigate to bare `/vault/`) → all documents shown.

### 10. Sidebar navigation — SC-007, FR-018

1. Log in → dashboard sidebar shows "Vault" link.
2. Click "Vault" → navigates to `/vault/` document list.
3. From any vault page, sidebar "Vault" link is active/visible.

### 11. Admin registration — FR-020

1. Log in as a superuser → navigate to `/admin/`.
2. Verify "Vault" section appears with Category, Subject, Document Type, and
   Document models listed and manageable.

## Edge-case spot checks (from spec § Edge Cases)

| Check | Expected |
|---|---|
| Delete category with 0 documents | Succeeds; category removed from list |
| Delete category with 3 documents | Blocked; inline error on confirm page; category intact |
| Delete subject with documents | Blocked; same behavior as category |
| Delete document type with documents | Blocked; same behavior as category |
| Create 100+ categories | All listed; no limit enforced; deterministic alphabetical order (R13) |
| Edit document while second browser has it open | Last-write-wins; `updated_at` reflects winning save (R13) |
| Submit document form with blank title | Inline field error; nothing persisted |
| Submit document form without selecting category/subject/type | Inline field errors on all three; nothing persisted |
| Submit taxonomy form with blank name | Inline field error; nothing persisted |
| Two users create documents with same title simultaneously | One succeeds; other gets duplicate-title error (IntegrityError race guard; R5) |
| Unauthenticated POST to `/vault/categories/new/` | HTTP 405, no state change (R12) |

## What "done" looks like (checklist)

- [ ] `manage.py check` — 0 issues (SC-004)
- [ ] `manage.py test vault` — zero failures (SC-005)
- [ ] `manage.py test` — zero failures across all apps (no regressions)
- [ ] Vault sidebar link appears in dashboard (SC-007, FR-018)
- [ ] Category CRUD works: create, list, edit, delete (FR-007)
- [ ] Subject CRUD works: create, list, edit, delete (FR-008)
- [ ] Document Type CRUD works: create, list, edit, delete (FR-009)
- [ ] Document CRUD works: create, list, detail, edit, delete (FR-010)
- [ ] Document list shows only owner's documents (SC-002, FR-012)
- [ ] Other user's documents return 404 (SC-002, R7)
- [ ] Duplicate name/title validation works (SC-006, FR-013, FR-014)
- [ ] Taxonomy delete blocked when documents reference entity (R1, R8)
- [ ] Document list filtering by category/subject/type works (User Story 6)
- [ ] Document title search works (User Story 6)
- [ ] Unauthenticated access redirects with zero content leakage (SC-003)
- [ ] CSRF rejection observed (FR-015)
- [ ] Admin registrations visible in `/admin/` (FR-020)
- [ ] Full vault flow completable in <3 minutes (SC-001)
