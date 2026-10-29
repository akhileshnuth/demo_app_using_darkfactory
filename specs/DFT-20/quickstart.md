# Quickstart Validation: DFT-20

## Prerequisites

- Work from the repository root.
- Git is installed.
- The Django environment is installed.
- Set a temporary non-empty `SECRET_KEY` for Django commands; never place a
  real key in a committed file.

## Validate ignore decisions

Run:

```bash
git check-ignore -v --no-index -- \
  db.sqlite3 db.sqlite3-shm db.sqlite3-wal db.sqlite3-journal \
  private_documents/root.bin private_documents/nested/file.bin \
  .env .env.local .env.example \
  server.pem credentials.p12 id_rsa_work signing.private-key
```

Expected result: every database, upload, environment, and explicitly named
credential path except `.env.example` prints a matching rule and source file.
`.env.example` prints no matching ignore rule.

Also verify the configured upload root and database location in
`./config/settings.py` remain the documented paths. Do not create or commit
real database, upload, or secret content.

## Validate repository status behavior

Use disposable empty files/directories if desired, then run:

```bash
git status --short
git status --ignored --short
git ls-files -- db.sqlite3 private_documents .env .env.example
```

Expected result: ignored artifacts do not appear in normal short status; they
may appear in `--ignored`; no database, upload, or secret file is listed by
`git ls-files`; `.env.example` remains eligible to be tracked.

## Validate secret loading

Run the planned focused settings regression tests and the existing Django suite
with a temporary environment value, for example:

```bash
SECRET_KEY='temporary-test-only-key' python -m pytest
```

Expected result: settings uses the supplied value, missing/empty configuration
fails closed according to the implementation contract, and the existing suite
passes. The implementation must not introduce a fallback committed key.

## Operational security check

Before merge, the responsible human/deployment owner must rotate or revoke the
historical development key and update deployment secrets. This cannot be
verified or completed by `.gitignore`; it is a separate release/security
action. Merge still requires the protected-`main` pull request, human review,
and CI.
