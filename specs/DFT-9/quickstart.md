# DFT-9 Quickstart Validation Guide

Run locally from the repository root after the human security-zone gate and implementation handoff.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py check
python manage.py migrate
python manage.py test
```

Create three authenticated users: owner, intended recipient, and unrelated user.

1. Create a checklist with three items; edit title/item, toggle completion, reorder, remove one, reload, and verify persistence (FR-001/002, SC-001).
2. Create a view invitation and a contribution invitation. Verify the intended authenticated recipient must accept, forwarded/expired/used/revoked tokens fail, view cannot mutate, contribution changes are attributed, and unrelated users see no resource (FR-003–006, SC-002/004).
3. Configure an emergency policy for selected checklist content and contact. Exercise verification/waiting, approval, denial, expiry, session duration, revocation, repeated/ineligible requests, and owner-unavailable release safeguards. Verify only designated content is exposed (FR-007–010, SC-002).
4. Trigger share, acceptance, contribution, revoke, emergency request/decision/use/expiry, and delivery-failure events. Confirm each has actor, target, action, time, outcome, notification history, and no protected content in messages (FR-011–016, SC-003/005/006).
5. Disable an optional category and verify suppression; confirm mandatory security notifications remain. Confirm failed delivery does not change authorization.
6. Submit invalid blank/oversized/unsupported data and concurrent stale edits; verify no partial invalid write and a clear conflict outcome (FR-017/018).
7. Run authorization and CSRF checks: anonymous redirects to login, unauthorized object paths do not disclose existence, revoked/expired access fails closed, and POST without a valid CSRF token returns 403 with no state change.

Implementation acceptance also requires migration review, `python manage.py check`, zero test failures, and human review of all `auth`/`pii`-zoned files. Exact retention/export/deletion and external-channel behavior must be approved before production release.
