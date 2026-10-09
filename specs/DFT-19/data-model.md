# DFT-19 Data Model

## Persistence impact

No database schema changes are required. The existing `vault.Document`
records, owner relationship, taxonomy relationships, timestamps, and ordering
remain unchanged.

## Document Page (derived view model)

The document list derives a page from the owner-scoped, filtered `Document`
queryset:

| Field | Type | Rules |
|---|---|---|
| `object_list` | ordered queryset/list of `Document` | Contains only the selected page; at most 20 records |
| `number` | positive integer | Current 1-based page; below-one requests normalize to 1 |
| `paginator.num_pages` | positive integer | Highest available page for the filtered result; no page exists for an empty result |
| `paginator.count` | non-negative integer | Count after owner scoping and active filters |
| `has_previous` / `has_next` | boolean | Boundary indicators for navigation availability |
| `previous_page_number` / `next_page_number` | positive integer | Present only when the corresponding boundary indicator is true |
| `query` | GET query parameters | Preserved on navigation except `page`, which is replaced |

## Query and validation rules

1. Restrict documents to the authenticated request user before counting or
   slicing.
2. Apply the existing search/filter parameters before pagination.
3. Keep the established document ordering stable; add a deterministic tie
   breaker if implementation inspection shows equal ordering timestamps.
4. Use a fixed page size of 20; there is no persisted or user-selected size.
5. A missing page means page 1. A non-numeric or below-one page resolves to
   page 1; an above-range page resolves to the highest page.
6. Empty results retain the existing empty-list presentation and have no
   pagination controls.
7. A new filter or sort query omits `page`, resetting pagination to page 1.

## Relationships and state

`Document Page` is not persisted and has no independent lifecycle. It is
recomputed for each GET request from `Document` records. If records change,
the next request recalculates the count: the requested page remains if valid,
otherwise it is clamped, or the empty state is shown when count is zero.
