# DFT-8 Web Contracts

All vault pages are server-rendered HTML and require authentication. State
changes use POST plus CSRF. Taxonomy writes additionally require `is_staff` or
`is_superuser`; unauthorized taxonomy writes return HTTP 403 (`PermissionDenied`)
without changing state.

## Routes

| Name | Method | Path | Contract |
|---|---|---|---|
| `vault:document_list` | GET | `/vault/` | Owner-scoped list; category, subject, type, title filters; pagination retained. |
| legacy document list | GET | `/vault/documents/` | Redirect to `/vault/`, preserving relevant query parameters. |
| `vault:document_create` | GET/POST | `/vault/documents/new/` | Create metadata record with all three classifications and optional notes/expiry. |
| `vault:document_detail` | GET | `/vault/documents/<pk>/` | Owner-only detail including classifications and expiry/reminder metadata. |
| `vault:document_update` | GET/POST | `/vault/documents/<pk>/edit/` | Owner-only partial lifecycle update; preserve unrelated fields and reminder behavior. |
| `vault:document_delete` | GET/POST | `/vault/documents/<pk>/delete/` | Owner-only confirmation and delete. |
| taxonomy list/create/update/delete | GET/POST | `/vault/categories/`, `/vault/subjects/`, `/vault/types/` and `/new/`, `/<pk>/edit/`, `/<pk>/delete/` | Authenticated reads; staff/admin writes; duplicate and dependency errors inline. |
| `vault:export_data` | GET | existing export path | Existing owner-scoped export contract remains unchanged. |

## Form contract

Required fields are title/name and all three document classifications. The
document form also exposes the existing optional `expiry_date`; it never exposes
the system-managed `reminder_sent_at`. Invalid,
stale, duplicate, or unauthorized input returns the form with inline errors and
does not persist a partial record. Taxonomy delete of an in-use row returns an
actionable dependency message. Document metadata forms retain the existing
expiry fields and do not render a file upload control.

## Response and isolation contract

Document lookups are filtered by current owner and return not-found for another
user's record. Taxonomy lists are shared and ordered consistently. Successful
creates/updates/deletes redirect to the relevant list/detail route. The legacy
list route must redirect rather than render a second canonical list.
