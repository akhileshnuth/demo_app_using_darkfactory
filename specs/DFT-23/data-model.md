# DFT-23 Data Model

The runtime model contract is restored in `./checklists/models.py`; the database
schema remains supplied by `./checklists/migrations/0001_initial.py`.

| Entity | Required fields and behavior |
|---|---|
| `Checklist` | Owner FK to `settings.AUTH_USER_MODEL` (`CASCADE`, `checklists`), title max 140, created/updated timestamps; ordering `-updated_at`; `item_count`, `completed_count`, `completion_percentage` (zero for no items), and active `shared_with`. |
| `ChecklistItem` | Checklist FK (`CASCADE`, `items`), text max 200, `is_complete=False`, position default 0, timestamps; ordering `position,id`; unique `(checklist, position)` named `uniq_item_position`. |
| `ChecklistShare` | Checklist/recipient FKs with migration related names, `shared_at`, `active`/`revoked` status; ordering `-shared_at`; unique `(checklist, recipient)` named `uniq_share`; status constants. |
| `EmergencyContact` | Owner/contact user FKs, `designated_at`; ordering `-designated_at`; unique `(owner, contact)` named `uniq_emergency_contact`; reject self-designation in model validation. |
| `EmergencyAccessRequest` | Owner/requester FKs, statuses `pending`, `approved`, `denied`, `auto_granted`, `cancelled`, requested/resolved timestamps and timeout deadline; ordering `-requested_at`; `is_resolved` and guarded `resolve(status)`. |
| `Notification` | Recipient FK, four migration-defined types, message max 280, read flag, created timestamp, nullable SET_NULL links to checklist/share/request; ordering `-created_at`. |

## Invariants

- Checklist deletion cascades to items and shares; notification links are nullable
  and set null on deletion.
- Active shares are read-only; emergency access remains governed by existing
  service state transitions.
- Empty item sets yield item count `0`, completed count `0`, and percentage `0`.
- No new authorization or optional-relation behavior is introduced.
