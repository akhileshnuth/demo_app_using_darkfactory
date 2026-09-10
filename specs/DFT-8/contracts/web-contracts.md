# DFT-8 Web Contracts — Vault Routes & Forms

**Source**: `/specs/DFT-8/spec.md` FR-001…FR-020; see also
[`/specs/DFT-8/data-model.md`](../data-model.md) for the entities these contracts
read/write and [`/specs/DFT-8/research.md`](../research.md) for design decisions.

Interface type: **server-rendered HTML web application** (no JSON API, no CLI).
All state-changing requests (POST) are CSRF-protected (FR-015); a missing/tampered
token yields **HTTP 403** before the view runs. All page loads require
authentication (FR-011); unauthenticated GETs redirect to login with zero content
leakage (SC-003).

## Settings contract (must hold, else routes below break)

| Setting | Value |
|---|---|
| `AUTH_USER_MODEL` | `accounts.User` |
| `LOGIN_URL` | `/accounts/login/` |
| `LOGIN_REDIRECT_URL` | `/dashboard/` |
| `LOGOUT_REDIRECT_URL` | `/accounts/login/` |
| `INSTALLED_APPS` | includes `"vault"` (FR-016) |
| `ROOT_URLCONF` | `"config.urls"` — includes `path("", include("vault.urls"))` (FR-017) |

## URL namespace

All vault routes live under `app_name = "vault"`. Template code references
vault URLs as `vault:entity_action` (e.g. `{% url 'vault:category_list' %}`).

## Routes — Taxonomy entities (shared across all users)

The three taxonomy entities (Category, Subject, DocumentType) share an identical
route pattern. `entity` below represents `category`, `subject`, or `type`
respectively; URL name prefixes are `category_`, `subject_`, or `type_`.

### Category routes

| URL name | Path | Methods | Description |
|---|---|---|---|
| `vault:category_list` | `/vault/categories/` | GET | List all categories |
| `vault:category_create` | `/vault/categories/new/` | GET/POST | Create category |
| `vault:category_update` | `/vault/categories/<int:pk>/edit/` | GET/POST | Edit category |
| `vault:category_delete` | `/vault/categories/<int:pk>/delete/` | GET/POST | Delete category (confirm) |

### Subject routes

| URL name | Path | Methods | Description |
|---|---|---|---|
| `vault:subject_list` | `/vault/subjects/` | GET | List all subjects |
| `vault:subject_create` | `/vault/subjects/new/` | GET/POST | Create subject |
| `vault:subject_update` | `/vault/subjects/<int:pk>/edit/` | GET/POST | Edit subject |
| `vault:subject_delete` | `/vault/subjects/<int:pk>/delete/` | GET/POST | Delete subject (confirm) |

### Document Type routes

| URL name | Path | Methods | Description |
|---|---|---|---|
| `vault:type_list` | `/vault/types/` | GET | List all document types |
| `vault:type_create` | `/vault/types/new/` | GET/POST | Create document type |
| `vault:type_update` | `/vault/types/<int:pk>/edit/` | GET/POST | Edit document type |
| `vault:type_delete` | `/vault/types/<int:pk>/delete/` | GET/POST | Delete document type (confirm) |

### Taxonomy auth gate

All taxonomy routes require authentication (FR-011). Unauthenticated GET →
**302 → `/accounts/login/?next=<path>`** with zero content leakage (SC-003).
Unauthenticated POST → **405 Method Not Allowed** (Django 5.2 behavior; R12).

Taxonomy entities are shared across all users (FR-012) — no per-user scoping.
Any authenticated user can list, create, edit, or delete any taxonomy entity.

### Taxonomy form fields

All taxonomy forms (`CategoryForm`, `SubjectForm`, `DocumentTypeForm`) share:

| Field | Type | Required | Constraints | Notes |
|---|---|---|---|---|
| `name` | `CharField` | yes | `max_length=100`, `unique=True` | FR-002/003/004; case-insensitive duplicate rejection in `clean_name` (R6) |
| `description` | `TextField` | no | `blank=True` | FR-002/003/004; optional |

### Taxonomy form validation

- **Empty name** → inline field error "This field is required." (FR-002/003/004
  acceptance: empty name rejected).
- **Case-insensitive duplicate name** → inline field error "A [category/subject/
  document type] with this name already exists." (FR-014; R6 `clean_name`
  `__iexact` check).
- **Exact duplicate name** (same case) → ModelForm `validate_unique()` produces
  "[Entity] with this Name already exists." (DB `unique=True`; FR-014).
- **Concurrent same-name creation** → one wins, other catches `IntegrityError`
  in `form_valid` and re-renders with duplicate error (R6 race guard).

### Taxonomy delete protection

Taxonomy delete views use `ProtectedDeleteMixin` (R8). When a taxonomy entity
has documents referencing it (FK `on_delete=PROTECT`; R1):

- **GET** confirm page renders normally with the entity name.
- **POST** delete → `ProtectedError` caught → confirm page re-renders with
  inline error: "This [category/subject/document type] has N document(s) and
  cannot be deleted." The entity is **not** deleted (R1, R8).

When a taxonomy entity has **no** referencing documents, the POST delete
succeeds → **302 → category/subject/type list**.

## Routes — Documents (per-user scoped)

| URL name | Path | Methods | Description |
|---|---|---|---|
| `vault:document_list` | `/vault/` | GET | List current user's documents (with optional filters) |
| `vault:document_create` | `/vault/documents/new/` | GET/POST | Create document |
| `vault:document_detail` | `/vault/documents/<int:pk>/` | GET | View document details |
| `vault:document_update` | `/vault/documents/<int:pk>/edit/` | GET/POST | Edit document |
| `vault:document_delete` | `/vault/documents/<int:pk>/delete/` | GET/POST | Delete document (confirm) |

### Document auth gate

All document routes require authentication (FR-011). Unauthenticated GET →
**302 → login**. Unauthenticated POST → **405** (R12).

Documents are scoped to the authenticated user (FR-012). The `OwnerQuerysetMixin`
(R7) filters all document querysets to `owner=request.user`. Requests for
another user's document PK resolve to **404** (existence not leaked; R7).

### Document form fields

| Field | Type | Required | Constraints | Notes |
|---|---|---|---|---|
| `title` | `CharField` | yes | `max_length=200` | FR-005; per-user unique (FR-013) |
| `category` | `ModelChoiceField(Category)` | yes | FK `on_delete=PROTECT` | FR-005; select from all shared categories |
| `subject` | `ModelChoiceField(Subject)` | yes | FK `on_delete=PROTECT` | FR-005; select from all shared subjects |
| `document_type` | `ModelChoiceField(DocumentType)` | yes | FK `on_delete=PROTECT` | FR-005; select from all shared document types |
| `notes` | `TextField` | no | `blank=True` | FR-005; optional free-text |

The `owner` field is **not** a form input — it is set automatically in
`DocumentCreateView.form_valid`: `form.instance.owner = self.request.user`
(FR-006, R4).

### Document form validation

- **Blank title** → inline field error "This field is required." (FR-005).
- **No category/subject/type selected** → inline field error (FR-005).
- **Case-insensitive duplicate title (same user)** → inline field error "You
  already have a document with this title." (FR-013; R5 `clean_title`
  `__iexact` check, excluding self on edit).
- **Concurrent same-title creation (same user)** → one wins, other catches
  `IntegrityError` in `form_valid` and re-renders with duplicate error (R5
  race guard; DB `UniqueConstraint(owner, title)`).
- **Different users may hold the same title** — the composite constraint is
  scoped to `owner` (FR-013).

### Document create (POST)

- **Success** → **302 → `/vault/`** (document list).
- **Failure** → re-render `200` with inline field errors (FR-019).

### Document update (POST)

- **Success** → **302 → `/vault/documents/<pk>/`** (detail page). The
  `updated_at` timestamp bumps automatically (R4).
- **Failure** → re-render `200` with inline field errors (FR-019).

### Document delete (GET confirm + POST)

- **GET** confirm page: shows document title, asks for confirmation.
- **POST** delete → **302 → `/vault/`** (document list). Nothing references
  a document, so no PROTECT issues (R1, data-model edge cases).

### Document list — filtering (User Story 6, R11)

`GET /vault/` accepts optional query parameters:

| Parameter | Type | Effect |
|---|---|---|
| `category` | integer (PK) | Filter to documents in that category |
| `subject` | integer (PK) | Filter to documents with that subject |
| `type` | integer (PK) | Filter to documents with that document type |
| `q` | string | Filter to documents whose title contains the search term (case-insensitive) |

- No parameters → full owner-scoped list ("clear all filters"; User Story 6
  acceptance 3).
- Multiple parameters compose with AND.
- Invalid/non-matching PK values → empty result set (safe, no error).
- The filter form uses `<form method="get">` — **no CSRF token** needed (GET
  only; FR-015 applies to state-changing methods).
- The list is ordered by `-updated_at` (most recently updated first; User Story 4
  acceptance 4; `Meta.ordering`; R4).
- `select_related("category", "subject", "document_type")` avoids N+1 queries.

### Document list context

The document list view provides to the template:
- `object_list` — the filtered, owner-scoped document queryset.
- `categories` — all `Category` objects (for filter `<select>`).
- `subjects` — all `Subject` objects (for filter `<select>`).
- `types` — all `DocumentType` objects (for filter `<select>`).
- `current_category`, `current_subject`, `current_type`, `current_q` — the
  current filter values (to pre-populate the `<select>`s and search input).

### Document detail view

`GET /vault/documents/<int:pk>/` renders a read-only detail page showing:
- Title
- Category name
- Subject name
- Document type name
- Notes (if any)
- Created timestamp
- Updated timestamp
- Edit and Delete action links

## HTTP status summary

| Route | Method | Auth | Success | Errors |
|---|---|---|---|---|
| `/vault/categories/` | GET | **required** | 200 list | 302 → login?next |
| `/vault/categories/new/` | GET/POST | **required** | 200 form / 302 → list | 302 → login?next; 200 + inline errors |
| `/vault/categories/<pk>/edit/` | GET/POST | **required** | 200 form / 302 → list | 302 → login?next; 200 + inline errors |
| `/vault/categories/<pk>/delete/` | GET/POST | **required** | 200 confirm / 302 → list | 302 → login?next; 200 + delete_error |
| `/vault/subjects/` | GET | **required** | 200 list | 302 → login?next |
| `/vault/subjects/new/` | GET/POST | **required** | 200 form / 302 → list | 302 → login?next; 200 + inline errors |
| `/vault/subjects/<pk>/edit/` | GET/POST | **required** | 200 form / 302 → list | 302 → login?next; 200 + inline errors |
| `/vault/subjects/<pk>/delete/` | GET/POST | **required** | 200 confirm / 302 → list | 302 → login?next; 200 + delete_error |
| `/vault/types/` | GET | **required** | 200 list | 302 → login?next |
| `/vault/types/new/` | GET/POST | **required** | 200 form / 302 → list | 302 → login?next; 200 + inline errors |
| `/vault/types/<pk>/edit/` | GET/POST | **required** | 200 form / 302 → list | 302 → login?next; 200 + inline errors |
| `/vault/types/<pk>/delete/` | GET/POST | **required** | 200 confirm / 302 → list | 302 → login?next; 200 + delete_error |
| `/vault/` | GET | **required** | 200 list | 302 → login?next |
| `/vault/documents/new/` | GET/POST | **required** | 200 form / 302 → list | 302 → login?next; 200 + inline errors |
| `/vault/documents/<pk>/` | GET | **required** | 200 detail | 302 → login?next; **404** (other user's doc) |
| `/vault/documents/<pk>/edit/` | GET/POST | **required** | 200 form / 302 → detail | 302 → login?next; 200 + inline errors; **404** |
| `/vault/documents/<pk>/delete/` | GET/POST | **required** | 200 confirm / 302 → list | 302 → login?next; **404** |
| any POST with bad/missing CSRF | — | — | — | **403** |
| any GET/POST to vault URL (unauthenticated) | GET → **302**, POST → **405** | — | — | zero content leakage |

## Template surface

All vault templates extend `templates/base.html` and render within the
authenticated shell (sidebar + header + main content block). Templates follow
the `{% block content %}` convention.

### Shared taxonomy templates (Category/Subject/DocumentType)

Three template patterns, instantiated three times each:

| Pattern | Purpose | Key template variables |
|---|---|---|
| `<entity>_list.html` | List all taxonomy entities with Create/Edit/Delete links | `object_list`, `entity_label` (e.g. "Category"), `entity_label_lower` (e.g. "category") for URL construction |
| `<entity>_form.html` | Create/Edit form with inline errors | `form`, `entity_label`, `entity_label_lower`, `object` (if editing) |
| `<entity>_confirm_delete.html` | Delete confirmation page | `object`, `entity_label`, `entity_label_lower`, `delete_error` (if PROTECT blocked) |

The templates use `entity_label` to render human-readable headings and
`entity_label_lower` to construct per-entity URLs dynamically:
`{% url 'vault:'|add:entity_label_lower|add:'_list' %}`.

### Document templates

| Template | Purpose | Key variables |
|---|---|---|
| `document_list.html` | List current user's documents with filter form | `object_list`, `categories`, `subjects`, `types`, `current_category`, `current_subject`, `current_type`, `current_q` |
| `document_form.html` | Create/Edit document form with inline errors | `form`, `object` (if editing) |
| `document_detail.html` | Read-only document detail page | `object` (Document instance) |
| `document_confirm_delete.html` | Delete confirmation page | `object` (Document instance) |

### Sidebar navigation (FR-018)

`templates/base.html` sidebar gains vault navigation links for authenticated
users:

```html
<li><a href="{% url 'vault:document_list' %}">Vault</a></li>
```

This is the only change to the existing `base.html` template. The vault
sub-pages (categories, subjects, types) are linked from within the vault
templates themselves, not from the sidebar.

## Non-contract surface (explicitly out of scope)

- No JSON/REST API; no schema/OpenAPI.
- No file upload or storage backend — documents are metadata records only (R2).
- No pagination — ListView handles all rows (R13).
- No optimistic locking or version fields (R13).
- No filtering or search beyond the document list (User Story 6 scope).
- `/admin/` is Django's stock admin for administrative management (FR-020), not
  part of this ticket's primary contract.
