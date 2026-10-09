# DFT-19 Web Contract

## Document list GET

- **Route**: existing namespaced `vault:document_list` document-list route
  (the repository's intended `/vault/` surface).
- **Authentication**: preserve the existing login requirement and owner
  isolation.
- **Query parameters**:
  - `page` — optional 1-based page number; not a document filter.
  - Existing document-list filters (`q`, `category`, `subject`,
    `document_type`) remain accepted and are preserved by pagination links.
- **Response**: existing server-rendered document-list HTML, with no more than
  20 rows from the filtered, owner-scoped result set.
- **Invalid page**: render page 1 for below-one/non-numeric input and the last
  available page for above-range input; render the existing empty state when
  there are no matching documents.

## Pagination controls

When more than one page exists, the response identifies the current page and
total pages and provides:

- first → `page=1`
- previous → immediately preceding page
- next → immediately following page
- last → highest available page

Each URL preserves all active non-page query parameters. First/previous are
unavailable on the first page, next/last are unavailable on the last page.
For zero or one page, no link to a nonexistent page is rendered.

## Filter reset

The existing GET filter form submits its query without `page`; changing or
clearing a filter therefore starts at page 1 while pagination links retain
the resulting filter query.
