# DFT-8 Research & Design Decisions

**Phase 0 output** — resolves all `NEEDS CLARIFICATION` items from the Technical
Context (see `./specs/DFT-8/plan.md`) and records best-practice decisions for the
document vault. Each entry follows *Decision / Rationale / Alternatives considered*.

Date: 2026-09-09

Related: DFT-7 research (`./specs/DFT-7/research.md`) established the Django 5.2
stack, the email-keyed `accounts.User` model, and the flat repo layout this ticket
builds on.

---

## R1. Delete behavior for referenced taxonomy entities (NEEDS CLARIFICATION resolved)

**Decision**: Deleting a Category, Subject, or DocumentType that has one or more
documents referencing it is **blocked**. The `Document` FK fields use
`on_delete=models.PROTECT`, and the taxonomy `DeleteView`s catch
`django.db.models.ProtectedError` and re-render the confirmation page with an
inline error ("This category has N documents and cannot be deleted."), leaving the
entity intact. Deleting an *unreferenced* entity succeeds normally.

**Rationale**: FR-005 requires every document to be linked to *exactly one*
category, subject, and type. `SET_NULL` would violate that (an orphaned document
would have a null FK) — the spec's own Assumptions prefer blocking with an error.
CASCADE is out of the question: taxonomy entities are shared across all users
(FR-012), so cascading would delete *other users'* documents as a side effect of
one user's delete — a correctness and privacy bug. PROTECT + handled
`ProtectedError` is the only option consistent with all three requirements.

**Alternatives considered**: `SET_NULL` (breaks exact-one invariant, silently
"unclassifies" documents); CASCADE (deletes other users' documents — unacceptable);
backend `RESTRICT` (same protection, but PROTECT surfaces `ProtectedError` which is
the documented pattern for DeleteViews; RESTRICT differs only in evaluation order
and adds nothing here).

## R2. "Documents" are metadata records only (NEEDS CLARIFICATION resolved)

**Decision**: A document is a **metadata record** — title, notes, category/subject/
type FKs, owner, timestamps. **No file upload, no storage backend, no attachment
field.** Confirmed by the spec's own Assumptions ("documents... refers to document
metadata records... File attachment handling is out of scope").

**Rationale**: FR-005 enumerates exactly the metadata fields and no file field.
Adding uploads would require a storage backend decision (filesystem vs S3-style),
size/type validation, and probably a novel dependency (e.g. Pillow for images) —
none of which the ticket requests and none of which is autonomy-eligible under
Constitution Principle V.

**Alternatives considered**: FileField + local media storage (scope creep, storage
decisions belong to a dedicated ticket); STORAGES wiring (unneeded).

## R3. Taxonomy entity shape — three co-equal models

**Decision**: Three standalone models — `Category`, `Subject`, `DocumentType` — in
the `vault` app, each with: `name = CharField(max_length=100, unique=True)` (FR-002
.. FR-004), `description = TextField(blank=True, default="")`, `created_at`
(auto_now_add), `updated_at` (auto_now), `Meta.ordering = ["name"]`, `__str__ =
name`. Shared resources: every authenticated user sees and manages all of them
(FR-012); no owner FK.

**Rationale**: The spec's Key Entities define them as independent classifications
(User Story 1 vs 2 vs 3; "Subjects are independent of categories"). Three separate
models keep each taxonomy independently maintainable and give documents three
explicit FKs (FR-005). Alphabetical ordering makes shared list/select rendering
deterministic.

**Alternatives considered**: A single polymorphic "taxonomy tag" model with a `kind`
field (denormalizes FR-002/003/004 which require distinct persisted entities with
independent validation; makes form/URL per-entity semantics awkward); a shared
abstract base model `TaxonomyBase(name, description, timestamps)` with the three
concrete models inheriting it (DRY but adds indirection for zero persistence
benefit — models must stay separate tables per the spec's entity definitions).

## R4. Document model, ownership, and constraints (FR-005, FR-006, FR-013)

**Decision**: `Document` in `vault`:

- `owner = FK(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name="vault_documents")`
- `title = CharField(max_length=200)` (required)
- `notes = TextField(blank=True, default="")` (optional)
- `category / subject / document_type = FK(..., on_delete=PROTECT, related_name="documents")`
- `created_at` (auto_now_add), `updated_at` (auto_now)
- `Meta.ordering = ["-updated_at"]` (User Story 4 acceptance 4: most recently
  updated first)
- `Meta.constraints = [UniqueConstraint(fields=["owner", "title"], name="unique_document_title_per_owner")]`

Owner CASCADE (deleting a user's account removes their documents — correct for
user-scoped data); taxonomy PROTECT (see R1). The composite `UniqueConstraint`
works on SQLite.

**Rationale**: Satisfies FR-005/FR-006/FR-013 exactly. `-updated_at` ordering is
the default for every queryset including the ListView, so acceptance 4 needs no
view code.

**Alternatives considered**: `unique_together = ("owner", "title")` — the modern
spelling is `UniqueConstraint`; both produce identical SQLite DDL.

## R5. Per-user title uniqueness mechanics (FR-013)

**Decision**: Three layers:

1. **DB**: `UniqueConstraint(fields=["owner", "title"])` — authoritative,
   race-safe backstop (case-sensitive on SQLite).
2. **Form**: `DocumentForm.clean_title` rejects case-insensitive duplicates for
   the current owner (`Document.objects.filter(owner=user, title__iexact=title)
   .exclude(pk=self.instance.pk)`) — "You already have a document with this
   title." The form receives the current user via a constructor kwarg.
3. **View**: `CreateView`/`UpdateView` `form_valid` wraps the save in
   `try/except IntegrityError` and re-renders with the duplicate-title error — the
   documented idiom for the concurrent-POST race where both requests pass the form
   check (spec Edge Case: "concurrent creation of documents with the same title").

Different users may hold the same title (FR-013's per-user scoping) — the composite
constraint + `filter(owner=...)` checks make that explicit.

**Rationale**: SQLite uniqueness is case-sensitive, so layer 2 supplies the
user-friendly case-insensitive rule (same precedent as DFT-7 R8 email handling);
layer 1 + 3 close the race. There is no Django 5.2 helper for the race — the
`IntegrityError` catch is the accepted idiom.

**Alternatives considered**: Case-sensitive uniqueness only (rejects "Contract"
after "contract" — surprising UX); relying on ModelForm's composite-constraint
validation (does not fire: `owner` is assigned in `form_valid`, *after* `full_clean`
runs, so `validate_unique()` sees `owner=None` — leaving only the raw DB error).

## R6. Global taxonomy name uniqueness mechanics (FR-014)

**Decision**: `unique=True` on each taxonomy `name` + a form-level case-insensitive
check in each taxonomy form's `clean_name`
(`Category.objects.filter(name__iexact=name).exclude(pk=self.instance.pk)`) plus
the same `IntegrityError` catch in the six taxonomy create/update views as the race
backstop.

**Rationale**: ModelForm `_post_clean → validate_unique()` already hard-validates
`unique=True` fields (yielding "Category with this Name already exists."), so the
DB + stock validation cover exact duplicates; the `iexact` check closes
case-variants the way DFT-7 R8 did for emails; the `IntegrityError` catch covers
concurrent creation.

**Alternatives considered**: DB-only uniqueness (case-variant dupes slip through);
backend-only case-insensitive collation (not portable to SQLite).

## R7. Per-user document scoping in views (FR-012, SC-002)

**Decision**: A shared `OwnerQuerysetMixin(LoginRequiredMixin)` whose
`get_queryset()` returns
`super().get_queryset().filter(owner=self.request.user)`, applied to the document
List, Detail, Update, and Delete views. Requests for another user's document
resolve through the filtered queryset and yield **HTTP 404** (the object "does not
exist" to the requester). The Create view assigns `form.instance.owner =
self.request.user` in `form_valid`.

**Rationale**: Filtering the queryset is the standard Django pattern and gives
404-without-leaking-existence for foreign documents, satisfying SC-002 (isolated
vaults, no cross-user leakage) with the fewest moving parts. 404 is preferable to
403: 403 reveals that the resource exists.

**Alternatives considered**: `get_object()` pk-based fetch + owner assertions (#404
by hand — more code, same result); 403 responses (leaks existence).

## R8. Delete-view protection UX (FR-019 spirit)

**Decision**: A `ProtectedDeleteMixin(DeleteView)` override:

```python
def form_valid(self, form):
    try:
        return super().form_valid(form)
    except ProtectedError:
        context = self.get_context_data(form=form)
        context["delete_error"] = "This X has documents and cannot be deleted."
        return self.render_to_response(context)
```

The confirm templates render `{% if delete_error %}` inline. No redirect, no flash
message dependency: the user stays on the page explaining why. Applied to the three
taxonomy delete views (document delete needs no protection — nothing references a
document).

**Rationale**: A stock `DeleteView` would propagate `ProtectedError` as HTTP 500.
Re-rendering the confirm page with the inline error matches the spec's
"deletion is blocked with an error message" assumption and keeps the error beside
the action (same UX rule as FR-019's inline form errors).

**Alternatives considered**: `django.contrib.messages` flash after redirect to the
list page (two requests, error separated from the action, requires messages
templates); letting the 500 surface (unacceptable).

## R9. View style: Django generic class-based views

**Decision**: `ListView` / `CreateView` / `UpdateView` / `DeleteView` /
`DetailView` with `ModelForm`s, consistent with `dashboard.views.DashboardView` and
the spec's Assumption ("Django's built-in class-based views... consistent with the
pattern established in the dashboard app"). Every form renders `{{ field.errors }}`
inline (FR-019; pattern already used by `templates/registration/signup.html`).
`LoginRequiredMixin` is the leftmost base of every view (FR-011).

**Rationale**: Class-based generics provide the CRUD surface with minimal code and
match the established repo pattern; `ModelForm` gives FR-019 inline server-side
errors for free.

**Alternatives considered**: Function views (more boilerplate per endpoint — 17
routes); DRF (JSON API not requested).

## R10. URL layout and namespacing

**Decision**: New `vault` app with `app_name = "vault"`; root `config/urls.py`
gains `path("", include("vault.urls"))` (same `""`-prefix convention as
`accounts`/`dashboard`). Routes (all login-required):

| URL name | Path |
|---|---|
| `vault:document_list` | `/vault/` |
| `vault:document_create` | `/vault/documents/new/` |
| `vault:document_detail` | `/vault/documents/<int:pk>/` |
| `vault:document_update` | `/vault/documents/<int:pk>/edit/` |
| `vault:document_delete` | `/vault/documents/<int:pk>/delete/` |
| `vault:{category\|subject\|type}_list` | `/vault/categories/`, `/vault/subjects/`, `/vault/types/` |
| `vault:{category\|subject\|type}_create` | `/vault/categories/new/`, ... |
| `vault:{category\|subject\|type}_update` | `/vault/categories/<int:pk>/edit/`, ... |
| `vault:{category\|subject\|type}_delete` | `/vault/categories/<int:pk>/delete/`, ... |

`/vault/` IS the document list (the vault landing page). The shared taxonomy
templates build per-entity URLs from a context `entity_label`
(`category`/`subject`/`type`) using Django's `|add:` filter against these stable
names.

**Rationale**: One namespace keeps the 17 names collision-free; singular verbs
(`_create`, `_update`, `_delete`, `_list`, `_detail`) match Django conventions.
`/vault/ = documents` matches User Story 4/6 which treat the document list as the
primary vault view.

**Alternatives considered**: Separate `/vault/documents/` list path with `/vault/`
as a redirect landing page (extra hop, no content benefit); no namespace (flat
names like `category_list` at root risk future collisions).

## R11. Filtering and search (User Story 6)

**Decision**: `DocumentListView.get_queryset()` inspects `self.request.GET`:

- `category`, `subject`, `type` → `filter(category_id=…)` etc. (FK `_id` filters
  avoid extra queries). Params are tolerated: parse as int, treat non-integer or
  blank input as "no filter" (returns empty result set only for a real, valid
  non-matching pk — silent empty list, which is correct and safe).
- `q` → `title__icontains` (stripped; blank → no filter).
- No params (or all empty) → full owner-scoped list ("clear all filters" = the bare
  URL, User Story 6 acceptance 3).
- `select_related("category", "subject", "document_type")` on the document queryset
  to avoid N+1 when rendering the three names per row.
- The filter UI is a plain `<form method="get">` — **no CSRF token** (CSRF protects
  state-changing methods only), a documented fact per FR-015.
- Context adds the three full shared taxonomy lists plus the current selections to
  pre-populate the `<select>`s.

**Rationale**: Pure-queryset filtering is the idiomatic ListView approach, combines
with FR-012's owner scoping and R7's mixin cleanly, and needs no form machinery for
a read-only filter surface.

**Alternatives considered**: FilterSets (third-party Django-Filter — novel
dependency, violates Principle V); session-stored filters (unnecessary state);
custom `ModelForm` for the GET filter (machinery without benefit).

## R12. Auth gating and the Django ≥5.0 POST nuance (FR-011, SC-003)

**Decision**: `LoginRequiredMixin` on all 17 views. For **unauthenticated** requests:

- **GET** (all page loads): `302` → `/accounts/login/?next=<full path>` — zero page
  content in the redirect response (SC-003).
- **POST** (create/update/delete submits from an expired session): Django ≥5.0's
  `LoginRequiredMixin` returns **HTTP 405 Method Not Allowed** instead of
  redirecting non-idempotent requests. This is standard Django 5.2 behavior (5.0
  release-notes change); redirecting a POST would resubmit it after login.

SC-003's literal wording ("result in a redirect to the login page") is measured on
the GET surface — every vault page load redirects with zero leakage. The POST
behavior is 405 with zero side effects (no state change, no leakage) and is
recorded here as the accepted, framework-mandated deviation.

**Related carryover observation**: the DFT-7 test
`accounts/tests.py::ProfileViewTests::test_profile_post_after_logout_redirects_to_login`
asserts a redirect for an unauthenticated POST — behavior that predates Django 5.0.
DFT-8 does not modify `accounts/`; the vault test suite must instead assert the
actual Django 5.2 behavior (405 for unauthenticated POST to a vault submit route)
and the implementer should verify on a live run which response the pinned Django
produces, recording the observed status in the PR (see R14 — local Python runs are
the authority).

**Alternatives considered**: Matching the literal SC-003 wording by forcing POST
redirects — would require overriding `LoginRequiredMixin` and contradicts Django's
safe-methods handling.

## R13. Limits and concurrency edge cases (spec § Edge Cases)

**Decision**:
- **Practical limit on taxonomy size / document count**: none enforced; no
  pagination in this ticket. SQLite and the ListView handle low-thousands of rows;
  `Meta.ordering` keeps lists deterministic. Documented disposition — a
  pagination/virtualization ticket is a future concern, not this one.
- **Concurrent editing of the same document**: last-write-wins. `updated_at` via
  `auto_now` reflects the winning save. No optimistic locking (would need a version
  field or `F()` gauntlets — out of scope, no requirement demands it).
- **Concurrent same-title creation (same user)**: DB `UniqueConstraint` + R5's
  `IntegrityError` catch → one request wins, the other re-renders with the
  duplicate-title error (no 500).
- **Concurrent same-name taxonomy creation**: same mechanism via R6.

**Rationale**: Each edge case has a concrete, tested disposition; none requires new
infrastructure.

**Alternatives considered**: Pagination (real scope addition with no requirement);
optimistic-lock version field (feature nobody asked for).

## R14. Verification strategy under the Python-overlay constraint

**Decision**: Tests use Django's bundled runner (`python manage.py test`, in-memory
SQLite). The implementer must run the suite locally and report results; the factory
sandbox ships Node only with no PyPI egress (`./overlays/python/README.md`), so
this ticket ships **UNVERIFIED** for the human approver, exactly as DFT-7 did.
SC-005's authority is the implementer's local run + the human reviewer.

**Rationale**: Same honest accounting DFT-7 used (R11 there); SC-005 remains
verifiable even though the factory pipeline cannot execute Python tests.

**Alternatives considered**: Skipping tests (violates Principle IV); fabricating
Node-based test evidence (fiction).

## R15. Security-zone mapping (Constitution Principle II) — DFT-7 carryover

**Decision**: The vault app introduces a **user-generated-content surface**: the
`Document` model's `title`/`notes` belong to an individual owner — personal data by
the constitution's own definition (the `pii` zone covers personal data; DFT-7 R12
already mapped the display name under `pii`). The end-state zone map should
therefore include a `vault/` row naming the document surface:

| Actual path (proposed end state) | Zone name | Why |
|---|---|---|
| `accounts/` auth/session logic | `auth` | (DFT-7 mapping, still unactioned) |
| `accounts/` Profile + dashboard display-name rendering | `pii` | (DFT-7 mapping, still unactioned) |
| `vault/models.py` Document (title/notes), document views/templates/users' documents | `pii` | User-generated personal data (new in DFT-8) |

**Why this ticket is not blocked**: principle enforcement runs from the factory's
zone map (`FACTORY_ZONES` / `agentguard/policies/zones/zones-v0.json`), which still
carries the template-default rows (`src/auth`, `src/payments`, `src/customers`) —
paths that do not exist in this repo. No declared zone matches `vault/` (or
`accounts/`), so agent writes are not denied, and the spec's Assumption ("the vault
does not touch any declared security zones") holds under the *currently declared*
map. DFT-7 deliberately deferred the map update and shipped UNVERIFIED with that
deferral recorded; DFT-8 continues that recorded deferral rather than silently
assuming zones.

**Action**: Updating `SECURITY_ZONES.md` rows to the real paths AND mirroring them
into the factory zone map is **human-gated follow-up work** — it must happen after
this ticket's vault code exists (otherwise the vault app becomes agent-denied
mid-ticket for the very PR being delivered). The implementer does **not** write to
`SECURITY_ZONES.md` in this ticket; the plan and this research note make the
decision explicit and reviewable so it cannot be mistaken for a default.

**Alternatives considered**: Declaring `vault/` a `pii` zone inside this ticket
(deadlocks the agent — mirroring mid-ticket denies the vault writes the ticket
exists to perform); silently proceeding with no record (violates "an empty zone map
must be a recorded decision, never a default").

---

## Dependency & integration notes

- **Django built-ins used**: `django.views.generic` (CBVs), `django.forms.ModelForm`,
  `django.contrib.auth.mixins.LoginRequiredMixin`, `django.urls.reverse_lazy`,
  `django.db` (`models`, `IntegrityError`, `ProtectedError`),
  `django.contrib.admin` (FR-020). No third-party packages — `requirements.txt`
  stays `Django~=5.2` (Principle V: autonomy-eligible).
- **Integrations**: none external. The vault reads `accounts.User`
  (`settings.AUTH_USER_MODEL`), the dashboard shell (`templates/base.html`) gains
  sidebar links only, and `config/` gains one app entry + one include — no app
  code changes outside `vault/` except the base template nav.