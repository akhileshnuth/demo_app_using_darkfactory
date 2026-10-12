# Quickstart Validation: Vault Export

## Prerequisites

From the repository root, install the existing requirements and initialize the
Django database using the project's normal setup. No new runtime dependency or
worker is required.

```text
python -m pip install -r requirements.txt
python manage.py migrate
```

Implementation validation is run with:

```text
python manage.py test
```

## End-to-end scenarios

1. Create two users, taxonomy records, and documents owned by each user.
2. Log in as user A and activate the export action from the document list.
3. Assert a `200` ZIP download with the headers in
   [contracts/export-download.md](./contracts/export-download.md).
4. Open the ZIP, parse `manifest.json` and `documents.json`, verify schema
   version, hashes, count, ISO values, and that only user A's records appear.
5. Repeat for an authenticated user with no documents; expect a valid archive
   and `document_count: 0` with an empty JSON array.
6. Request the route anonymously; expect login denial/redirect and no ZIP body.
7. Exercise serialization/size-limit failure; expect a non-success response,
   no attachment headers, and actionable retry guidance.
8. Change data after snapshot materialization in a controlled test and verify
   the package represents the documented single snapshot rather than a mixed
   set.

## Review checklist

- `python manage.py test` is green in CI.
- The old references to nonexistent `Document.file` and `issue_date` are gone.
- No migration, export file, temporary path, or generated vault content is
  written under the repository or a declared security-zone path.
- The user-facing documentation identifies the ZIP/JSON format and explicitly
  says attachments are not included in schema version 1.
