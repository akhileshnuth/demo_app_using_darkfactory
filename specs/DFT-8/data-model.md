# DFT-8 Data Model — Document Vault Core

**Source**: `./specs/DFT-8/spec.md` § Key Entities + FR-002 … FR-006, FR-012, FR-013, FR-014

Decisions underlying this model are in `./specs/DFT-8/research.md`: delete
protection via `PROTECT` (R1), metadata-only documents (R2), three co-equal
taxonomy models (R3), composite per-owner title constraint (R4, R5), case-insensitive
duplicate handling (R5, R6). The vault references the DFT-7 `accounts.User` model
(`AUTH_USER_MODEL = "accounts.User"`); it does not modify it.

---

## Entities

### 1. Category — `vault.models.Category`

Top-level organizational unit. Shared across all users (FR-012).

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `BigAutoField` | PK | implicit (DEFAULT_AUTO_FIELD) |
| `name` | `CharField` | `max_length=100`, `unique=True`, required | FR-002; global uniqueness FR-014; case-insensitive dupes rejected in form (R6) |
| `description` | `TextField` | `blank=True`, `default=""` | optional (FR-002) |
| `created_at` | `DateTimeField` | `auto_now_add` | FR-002 created timestamp |
| `updated_at` | `DateTimeField` | `auto_now` | FR-002 updated timestamp |

**Relationships**: `documents` (reverse FK from `Document.category`; PROTECT — an
in-use category cannot be deleted, R1).

**Meta**: `ordering = ["name"]` (deterministic shared lists/selects). `__str__ = name`.

### 2. Subject — `vault.models.Subject`

Topic within the vault. Shared (FR-012). Identical field shape to Category
(FR-003): `name` (unique, required), `description` (optional), `created_at` /
`updated_at`. Reverse FK `documents` (PROTECT). `Meta.ordering = ["name"]`.

### 3. DocumentType — `vault.models.DocumentType`

Classification label. Shared (FR-012). Identical field shape (FR-004): `name`
(unique, required), `description` (optional), timestamps. Reverse FK `documents`
(PROTECT). `Meta.ordering = ["name"]`.

### 4. Document — `vault.models.Document`

The central vault entity: a **metadata record** (no file upload — R2), scoped to
its owner (FR-006, FR-012).

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `BigAutoField` | PK | implicit |
| `owner` | `FK(User)` | `on_delete=CASCADE`, `related_name="vault_documents"` | FR-006; deleting the account deletes its documents (user-scoped data) |
| `title` | `CharField` | `max_length=200`, required | FR-005; composite uniqueness below (FR-013) |
| `notes` | `TextField` | `blank=True`, `default=""` | optional (FR-005) |
| `category` | `FK(Category)` | `on_delete=PROTECT`, `related_name="documents"` | FR-005 "exactly one"; deletion blocked while referenced (R1) |
| `subject` | `FK(Subject)` | `on_delete=PROTECT`, `related_name="documents"` | FR-005 |
| `document_type` | `FK(DocumentType)` | `on_delete=PROTECT`, `related_name="documents"` | FR-005 |
| `created_at` | `DateTimeField` | `auto_now_add` | FR-005 |
| `updated_at` | `DateTimeField` | `auto_now` | FR-005; drives sort order |

**Meta**:
- `ordering = ["-updated_at"]` — User Story 4 acceptance 4 (most recently updated
  first) with no view code.
- `constraints = [UniqueConstraint(fields=["owner", "title"], name="unique_document_title_per_owner")]`
  — FR-013 (per-user title uniqueness; different users may share titles).

**Diagram**:

```text
User (accounts, unchanged)
  │ 1                1..*                1..*
  └──<owner/─ Document ──category──> Category        (shared)
                    │──subject──────> Subject        (shared)
                    │──document_type> DocumentType   (shared)
            title, notes, created_at, updated_at
```

**State transitions**:

```text
(no taxonomy rows) → create Category/Subject/DocumentType → create Document
  → view (list/detail/filter) → edit → updated_at bumps, sorts to top
  → delete (owner only, always allowed)
  → delete a referenced Category/Subject/DocumentType → BLOCKED (inline error)
  → delete a user account → CASCADE removes that user's documents only
```

Lifecycle is plain CRUD; there is no workflow (no draft/published states) in scope.

---

## Validation rules (mapped from requirements)

| Rule | Requirement | Enforcement point |
|---|---|---|
| Taxonomy `name` required | FR-002/003/004 (acceptance: empty name rejected) | `CharField(required=True)` on model + form (strip → blank becomes invalid) |
| Taxonomy `name` unique globally (case-sensitive exact) | FR-014 | DB `unique=True` + ModelForm `validate_unique()` ("…with this Name already exists.") |
| Taxonomy `name` unique globally (case-insensitive) | FR-014 (UX rule) | Form `clean_name` `__iexact` check, excluding self on edit (R6) |
| Document `title` required | FR-005 (User Story 4/5 acceptance) | Model + form required (blank → inline field error) |
| Document `category`/`subject`/`document_type` all required | FR-005 (missing selection → inline error) | ModelForm `ModelChoiceField(required=True)` for the three FKs |
| Document title unique per owner (case-insensitive) | FR-013 | Form `clean_title` `filter(owner=user, title__iexact=title)` excluding self (R5) |
| Document title unique per owner (race-safe) | Edge case: concurrent same-title creation | DB `UniqueConstraint(owner, title)` + `IntegrityError` catch in create/update views (R5) |
| Owner set automatically | FR-006 | `form.instance.owner = self.request.user` in `DocumentCreateView.form_valid`; never form-inputtable |
| Owner-only access to documents | FR-012 (SC-002) | `OwnerQuerysetMixin.get_queryset() → filter(owner=request.user)` on list/detail/update/delete (R7) |
| No deleting an in-use taxonomy entity | Edge cases + spec Assumption | FK `on_delete=PROTECT` + `ProtectedDeleteMixin` inline error (R1, R8) |
| CSRF on all state-changing vault POSTs | FR-015 | Django CSRF middleware + `{% csrf_token %}` in all POST forms; GET filter form needs none (R11) |
| Login required on all vault views | FR-011 | `LoginRequiredMixin` leftmost on every vault view (R12) |

All form validation is server-side and renders inline next to fields (FR-019)
via `{{ field.errors }}`, the pattern already used in `templates/registration/signup.html`.

---

## Edge-case dispositions (from spec § Edge Cases)

| Edge case | Behavior |
|---|---|
| Delete a category/subject/type that has documents | **Blocked** — confirm page re-renders with inline error: "This X has N documents and cannot be deleted."; nothing deleted (R1, R8) |
| Delete a category/subject/type that has no documents | Allowed; row removed (FKs from *other* taxonomy kinds unaffected) |
| Delete a document | Allowed; owner-only via filtered queryset (R7); nothing references documents so no PROTECT issues |
| Very large number of categories/subjects/types | No enforced limit; no pagination in scope; deterministic ordering; documented limitation (R13) |
| Document edited while another user views it | Last-write-wins; `updated_at` reflects the winning save; no versioning/locking (R13) |
| Concurrent creation of same-title documents (same user) | One wins; other re-renders with duplicate-title error via `IntegrityError` catch (R5, R13) |
| Concurrent creation of same-name taxonomy rows | Same mechanism via R6 |
| File attachment upload | Out of scope — documents are metadata-only records (R2) |
| Unauthenticated POST to a vault submit route | HTTP 405 (Django ≥5.0 `LoginRequiredMixin`; R12) |
| Unauthenticated GET to any vault URL | 302 → `/accounts/login/?next=<path>`, zero content in the redirect (SC-003, R12) |
| Non-owner requests another user's document | 404 (filtered queryset, existence not leaked; R7) |