# Export Download Contract

## User-facing route

`GET /export/` (Django route name: `vault:export_data`)

The existing route remains authenticated and is linked from the vault document
list. It represents both preparation and download for the synchronous design.

### Success: `200 OK`

- `Content-Type: application/zip`
- `Content-Disposition: attachment; filename="vault-export.zip"`
- `Content-Length`: complete archive byte length
- `Cache-Control: no-store`
- `X-Content-Type-Options: nosniff`
- body: ZIP package defined in [data-model.md](../data-model.md), with
  `manifest.json` and `documents.json`.

### Authentication and isolation

- Anonymous requests are redirected/denied by Django's existing login-required
  behavior and never receive export bytes.
- The queryset is scoped to `request.user`; there is no user or document ID
  parameter in the route.
- No other user's documents or account records may appear in the package.

### Failure contract

For generation, validation, size-limit, or response-preparation failure, return
an explicit non-2xx error or safe rendered error message with retry guidance.
Do not set attachment headers, `application/zip`, or a success status. Do not
expose exception text, filesystem paths, or exported content. A retry is
appropriate for transient preparation failures; an over-limit failure should
direct the user to support/an approved future asynchronous export instead of
pretending a partial package is valid.

## Package contract

`manifest.json` declares format/version, snapshot metadata, included field
policy, document count, and member hashes. `documents.json` is a JSON array of
the approved current `Document` fields. Dates/timestamps use ISO forms and
null remains null. The package is portable without Django and contains no
attachments in schema version 1.
