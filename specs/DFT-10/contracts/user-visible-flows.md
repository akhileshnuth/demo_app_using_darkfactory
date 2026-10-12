# User-visible test contracts

These are the behavior contracts the implementation tests. They describe
observable inputs and outcomes, not implementation bodies.

| Surface | Success contract | Non-success/dependency contract |
|---|---|---|
| Accounts signup/login/profile/activity | Valid signup creates user/profile and redirects/logs in; login records login activity; profile and activity are current-user scoped | Invalid password/duplicate email is rejected; anonymous protected routes redirect; profile cannot target another user |
| Dashboard | Authenticated user receives dashboard and navigation | Anonymous user is redirected to login |
| Checklist CRUD/items | Owner can create/list/detail/edit/toggle/delete with expected state and template response | Anonymous/non-owner mutation is rejected; empty/invalid forms are rejected; shared/emergency access is read-only and scoped |
| Checklist sharing | Owner can share/revoke, recipient can view active share, activity/notification state is created | Unknown recipient, duplicate share, revoked share, and non-owner management follow existing error/authorization behavior |
| Emergency access | Contact can request and owner can approve/deny; expiry auto-grant and removal transition state correctly | Self-contact, unauthorized response, duplicate/pending request, and denied/revoked access are rejected or inaccessible |
| Notifications | Recipient lists, reads, read-all, and clear operate only on recipient-owned notifications | Other users cannot read or mutate notifications; unsafe redirect targets are not followed |
| Vault list/export | Authenticated owner sees only own documents; filters, pagination, and export response are deterministic for supported data | Anonymous access redirects; foreign documents are excluded; export dependency/model error is captured without live storage |
| Expiry reminders | Eligible unreminded documents send through locmem backend and mark sent | Already-reminded/ineligible documents are skipped; send failure does not falsely mark success |

The implementation must not invent routes referenced by vault templates but not
wired in `vault/urls.py`; those are recorded as assumptions or follow-up work.
