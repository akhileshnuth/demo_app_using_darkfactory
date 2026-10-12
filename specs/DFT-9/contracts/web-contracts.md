# DFT-9 Web Contracts

Interface: authenticated, server-rendered HTML mounted through `./config/urls.py`. All POST mutations require CSRF and use PRG redirects. Unauthorized resources return an indistinguishable 404 (or generic denial where a resource is not resolved); no protected metadata is included in errors.

## Checklist routes

- `GET/POST /checklists/` — owner list/create entry point.
- `GET/POST /checklists/<id>/` — detail and permitted item operations; owner and contributors see mutation controls appropriate to permission.
- `POST /checklists/<id>/title/` — validated title update with version/conflict response.
- `POST /checklists/<id>/items/` — add item.
- `POST /checklists/<id>/items/<item_id>/edit/`, `/toggle/`, `/delete/` — owner/contributor authorization, attribution, and conflict-safe updates.
- `POST /checklists/<id>/reorder/` — transactional ordered item IDs/version.
- `GET/POST /checklists/<id>/delete/` — owner-only delete with pending-access consistency.

## Sharing routes

- `GET/POST /checklists/<id>/share/` — owner creates an invitation with recipient, permission, and expiry; no anonymous links.
- `GET/POST /shares/<token>/accept/` — authenticated intended recipient only; validates hash, expiry, single use, checklist, and permission before activation.
- `POST /checklists/<id>/share/<grant_id>/revoke/` — owner/admin policy authorization; invalidates invitation/grant.
- `GET /checklists/shared/` — only active grants for the current user, with permission label.

## Emergency routes

- `GET/POST /emergency/policies/` and `/emergency/policies/<id>/` — owner configures contacts, designated content, verification, release/waiting rule, duration, and revocation.
- `POST /emergency/requests/` — eligible contact starts a request; rate limits and audits repeats.
- `POST /emergency/requests/<id>/approve/` and `/deny/` — authorized owner/administrator guarded decisions.
- `GET /emergency/sessions/<id>/` — eligible requester sees only designated content while session is active; expired/revoked sessions fail closed.
- `POST /emergency/sessions/<id>/revoke/` — owner/authorized administrator revokes access.

## Notifications and audit

- `GET/POST /notifications/` — recipient-scoped paginated history; safe actor/action/checklist/time details and delivery status.
- `POST /notifications/<id>/read/`, `/notifications/read-all/` — recipient-only read state changes; history remains available.
- `GET/POST /notifications/preferences/` — optional categories/channels only; mandatory security categories are immutable.
- `GET /security-events/` — authorized owner/admin audit view, filtered to permitted events and sanitized metadata.

## Common outcomes

Valid mutation: 302 PRG and success message. Invalid data: 200 form with useful field error and no state change. Expired/revoked/used invitation or access: generic denial and security event. Concurrent version conflict: 409 or 200 conflict form, with retained version and retry guidance. Delivery failure: authorization remains unchanged; notification history shows failed status and authorized reviewer visibility.
