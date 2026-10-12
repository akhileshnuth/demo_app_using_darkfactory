# DFT-8 Quickstart Validation

Prerequisites: Python 3.11+, an activated virtualenv, and
`pip install -r requirements.txt`.

```bash
python manage.py check
python manage.py migrate
python manage.py test
```

Expected: system checks and the full suite pass, including existing expiry,
pagination, and export tests.

## Manual acceptance flow

1. Create a normal user and a staff/superuser. Confirm anonymous `GET /vault/`
   redirects to login and does not expose vault content.
2. As staff, create, edit, list, and delete a category, subject, and document
   type. Confirm blank and case-insensitive duplicate names are rejected.
3. As the normal user, create a document with all three classifications, notes,
   and an expiry date. Confirm `/vault/` lists it with classifications and
   expiry metadata, and detail/edit/delete work.
4. Confirm `/vault/documents/` redirects to `/vault/`; filters by each taxonomy
   return only matching owner documents; pagination and export still work.
5. Confirm a second user cannot see or address the first user's document, while
   shared taxonomy remains selectable.
6. Attempt to delete a referenced taxonomy record. Confirm an actionable error,
   no deletion, and no document mutation. Delete an unreferenced row successfully.
7. Run the expiry reminder command using the existing test setup and confirm
   `expiry_date`/`reminder_sent_at` behavior remains unchanged.

Detailed entity rules are in [`./data-model.md`](data-model.md), and route/form
expectations are in [`./contracts/web-contracts.md`](contracts/web-contracts.md).
