# DFT-19 Pagination Validation Guide

## Prerequisites

- Python environment with the repository's Django 5.2 dependency installed.
- SQLite development/test database configured by `config/settings.py`.
- An authenticated user and at least 41 documents owned by that user, plus
  optional documents owned by another user to verify isolation.

## Automated validation

Run the Django suite from the repository root:

```bash
python manage.py test
```

The implementation phase should cover the cases listed in
[`./specs/DFT-19/data-model.md`](data-model.md) and this manual flow.

## Manual end-to-end flow

1. Sign in and open the existing `vault:document_list` route.
2. With 41 documents, verify page 1 has 20 rows, identifies page 1 of 3,
   exposes next/last, and does not offer previous/first navigation.
3. Follow next and verify rows 21–40; follow last and verify row 41 only.
   Confirm no adjacent page duplicates.
4. From the last page, verify next/last are unavailable; return with
   previous and first and verify the expected subsets.
5. Apply a search/category/subject/type filter while on a later page. Verify
   the result starts at page 1 and pagination links retain every active filter.
6. Request `?page=999` and `?page=0`; verify the response shows the last and
   first valid page respectively rather than an error or invalid empty page.
7. Remove enough records to invalidate the current page, reload, and verify
   clamping. Remove all matching records and verify only `No documents found.`
   appears with no pagination controls.
8. Verify an empty result, exactly 20 records, and fewer than 20 records do
   not expose links to nonexistent pages.

## Contract references

See [`./specs/DFT-19/contracts/web-contracts.md`](contracts/web-contracts.md)
for the request/response and control contract, and
[`./specs/DFT-19/data-model.md`](data-model.md) for derived page semantics.
