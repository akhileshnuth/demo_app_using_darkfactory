# Quickstart Validation: Protected Uploaded Documents

## Prerequisites

1. Install the existing dependency set (`Django~=5.2`) and run from the repository root.
2. Configure a temporary private document root outside static/public directories and a test database.
3. Apply migrations. Do not use a public web-server mapping for the private root.

## Automated validation

Run the existing Django suite plus the feature tests using the repository's supported environment:

```text
PYTHONPATH=./.pip_deps python manage.py test
```

The implementation should add focused coverage for the contracts in `./specs/DFT-17/contracts/document-access.md`, including owner/collaborator success, anonymous redirect, authenticated non-disclosing 404, guessed/altered IDs, direct filesystem-path bypass, pending/expired/deleted/missing/corrupt files, partial upload cleanup, audit contents, audit failure, and orphan cleanup.

## Manual end-to-end scenario

1. Create users A, B, and C; create an upload as A with B as an explicit collaborator.
2. Confirm the file is absent from static/public URL space and that the document is not `ready` until private storage and policy are committed.
3. Retrieve as A and B; verify exact bytes, attachment response, and an allowed audit record.
4. Retrieve as C and anonymously; verify no bytes, authenticated `404`, login redirect, and denied audit records (anonymous has null actor).
5. Try the storage key, guessed ID, altered ID, and any legacy/static path directly; verify no bypass or existence disclosure.
6. Remove B's collaborator row and retry; verify the current policy is enforced. Set expiry to today and retry; verify the same `404`.
7. Delete the document and run cleanup; verify bytes are removed or quarantined and retrieval remains unavailable.
8. Inject an audit write failure on an otherwise allowed request; verify the endpoint returns no document bytes.
9. Run inventory/re-protection in dry-run mode, review the recorded legacy exposure decision, and verify unresolved legacy rows remain unavailable.

## Rollout validation

Before enabling retrieval in an environment, require a complete inventory, verified protected replacements for every retrievable legacy item, no public/static mapping to the private root, and an operator-approved exposure-handling record. Re-run orphan/inventory checks after cutover.
