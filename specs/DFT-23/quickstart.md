# DFT-23 Validation Guide

## Prerequisites

Use a Python environment with `./requirements.txt` installed.

## Steps

1. Inspect `git diff --name-status`; only the planned model restoration and test
   deletions may appear.
2. Run `python manage.py check`; expect no system-check errors.
3. Run `python manage.py makemigrations checklists --check`; expect no pending
   changes. Add a migration only for a genuine reported schema mismatch.
4. Start the normal Django application and open authenticated `/checklists/`;
   expect the existing list or empty state, not a missing-model exception.
5. Open a zero-item checklist and a populated checklist; verify existing counts,
   percentage, and item operations render normally.
6. Exercise existing share, emergency, and notification entry points to confirm
   model resolution and nullable related links.
7. Verify no tracked test files remain under the approved path/name convention,
   while runner configuration remains present.

See `./data-model.md` for entity details and
`../DFT-9/contracts/web-contracts.md` for the preserved route contract.
