# DFT-19 Research & Design Decisions

Date: 2026-10-09

## R1. Pagination implementation

**Decision**: Use Django's built-in `ListView` pagination with a fixed
`paginate_by = 20` on the document list. Apply owner scoping and all existing
filters before pagination, and use the existing `Document` ordering with a
deterministic primary-key tie-breaker where needed.

**Rationale**: Django's `Paginator` and `Page` expose the required page
numbers, boundaries, and first/previous/next/last targets without a runtime
dependency or new persistence model. Filtering before pagination makes page
counts and the 20-item limit describe the active result set.

**Alternatives considered**: Client-side slicing (loads all documents and
does not scale); a third-party filtering/pagination package (unnecessary and
would violate the no-novel-dependency rule); a custom paginator (duplicates
stable Django behavior).

## R2. Invalid and changing page behavior

**Decision**: Resolve the requested `page` with Django's safe paginator
behavior, normalizing values below 1 to page 1 and clamping values above the
last page to the highest available page. An empty result uses the existing
`No documents found.` state and renders no controls. Re-evaluate the count on
each request so additions and removals naturally preserve a still-valid page
or clamp an invalid one.

**Rationale**: This directly implements the clarified behavior and avoids
404s or empty invalid pages. The current page remains unchanged when it is
still in range.

**Alternatives considered**: Returning 404 for malformed/out-of-range pages
(contradicts FR-007); redirecting every invalid page (adds a request and can
lose query state); showing an empty page (violates the edge cases).

## R3. Query-string preservation and reset

**Decision**: Treat `page` as the pagination parameter. Generate all
pagination URLs by copying the current GET query and replacing only `page`,
thereby preserving `q`, `category`, `subject`, and `document_type` filters.
The filter form submits without a `page` parameter, so a changed filter or
sort query starts at page 1. No user-selectable page size is added.

**Rationale**: This preserves the existing document-list filtering contract
without hard-coding future query parameters into every link. A GET form
submission that omits page is the simplest reset mechanism.

**Alternatives considered**: Hard-coded query strings (drops active filters);
session-stored pagination (unnecessary server state); a page-size control
(explicitly excluded by the approved specification).

## R4. Navigation and presentation contract

**Decision**: Extend `templates/vault/document_list.html` with accessible
first, previous, next, and last links. Render current page and total pages
when pagination applies; disable or omit first/previous on page 1 and
next/last on the final page, and omit the entire navigation region for empty
or single-page collections. Continue using the existing table and empty-list
copy.

**Rationale**: These controls and boundary states exactly match the approved
clarifications and keep existing document information unchanged.

**Alternatives considered**: Numbered-page-only controls (not requested);
always-visible links (allows navigation to nonexistent pages); replacing the
existing empty state (unnecessary behavior change).

## R5. Integration seam and dependencies

**Decision**: Implement pagination in the existing vault document-list view
in `vault/views.py`, with URL wiring in `vault/urls.py`/`config/urls.py` only
where required to expose the existing `/vault/` list. Use `select_related`
for the rendered taxonomy names. Add no migrations and no dependency changes.

**Rationale**: The repository is a Django 5.2 server-rendered application;
the existing document template is the established surface. Current checkout
has an incomplete vault view/URL scaffold, so the implementation plan must
restore the list integration as part of making pagination reachable rather
than assume a complete pre-existing `DocumentListView`.

**Alternatives considered**: Introducing an API/JavaScript paginator (new
surface and complexity); changing the `Document` schema (pagination is a
query concern); adding Django-filter or another package (not needed).

## R6. Verification approach

**Decision**: The implementation phase must add/adjust Django tests for page
boundaries, filter preservation, invalid-page clamping, empty/single-page and
exact-boundary collections, owner isolation, and no duplicates across pages.
Validation scenarios are recorded in `quickstart.md`; this planning phase
does not create test files.

**Rationale**: These cases map directly to FR-001..FR-008 and SC-001..SC-004
and satisfy the constitution's test-first requirement without changing
source during planning.

**Alternatives considered**: Manual browser checking only (insufficient for
boundary and ownership regressions); testing only the paginator class (misses
query preservation and rendered controls).
