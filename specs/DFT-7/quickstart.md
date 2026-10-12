# DFT-7 Quickstart

This guide validates the contracts in [`./contracts/web-contracts.md`](contracts/web-contracts.md)

## Prerequisites

- Python 3.11+ and a clean checkout of branch `DFT-7-scaffold-django-project`.
- From the repository root: `python -m venv .venv`, activate it, then
  `pip install -r requirements.txt`.
- Complete the human-gated auth/PII zone mapping before implementation changes.

## Setup and automated validation

```bash
python manage.py check
python manage.py makemigrations --check
python manage.py migrate
python manage.py test
```

Expected: no system-check issues, no unapplied model changes, migrations
complete, and zero test failures. The factory Python overlay cannot execute
these commands; local output is the human verification evidence.

## Manual journey checks

1. Open `/accounts/signup/`, submit a valid email and password, and confirm a
   redirect to `/dashboard/` in at most three visible steps.
2. Submit invalid email, weak/mismatched passwords, and duplicate email. Confirm
   inline errors and no invalid account creation.
3. POST logout, log back in, and confirm the dashboard is reachable again.
4. Open `/profile/`, save a display name, reload, and confirm it persists and is
   shown in the authenticated shell. Submit blank/overlong values and confirm
   no invalid save.
5. In an anonymous session, request `/dashboard/` and `/profile/`. Confirm a
   login redirect with `next` and no private content; confirm bad/missing CSRF
   tokens on POST return 403.

Record the command output and observed route results in the implementation PR;
the factory should label the Python verification UNVERIFIED until a human
reviews that evidence.
