# Research: DFT-20 Repository Ignore Rules

## Decision: Extend the existing root ignore file

`./.gitignore` already exists and is already tracked. The implementation should
extend it rather than create a second file. Existing factory, Python, and
credential rules must be preserved.

**Rationale:** Git uses the root file already in the repository, and the
specification's "exactly one root-level `.gitignore`" outcome is satisfied by
modifying that file.

**Alternatives considered:** Creating another ignore file is invalid; replacing
the file risks dropping existing factory/toolchain rules.

## Decision: Use explicit, root-anchored SQLite rules

The live `./config/settings.py` configures SQLite at `./db.sqlite3`. Add or
retain rules for exactly:

- `/db.sqlite3`
- `/db.sqlite3-shm`
- `/db.sqlite3-wal`
- `/db.sqlite3-journal`

**Rationale:** SQLite creates the sidecars during WAL, shared-memory, and
journal operations. Anchoring avoids ignoring unrelated nested databases and
makes the supported location auditable.

**Alternatives considered:** `*.sqlite*` is too broad; `db.sqlite3*` is less
explicit about the supported artifacts.

## Decision: Ignore only the repository-local upload root

The live settings default `PRIVATE_DOCUMENT_ROOT` to `./private_documents/`,
while allowing an external override. Ignore `/private_documents/` recursively.

**Rationale:** A trailing slash covers root files and nested upload content.
Git cannot protect an override outside the repository, and adding generic
`uploads/` or `media/` rules would not reflect the application's configured
storage.

**Alternatives considered:** Unanchored `private_documents` could hide
unrelated directories; generic upload/media rules are unsupported by current
configuration.

## Decision: Preserve the existing local secret filename policy

Keep `.env`, `.env.*`, and `!.env.example`, plus only the explicitly named
credential patterns already present: `*.pem`, `*.p12`, `*.key`, `id_rsa*`, and
`*.private-key*`. No example file currently exists, but the exception must
remain available for a future safe template.

**Rationale:** This meets the clarified naming convention without hiding
legitimate source/configuration files.

**Alternatives considered:** Broad `*secret*`, `*credentials*`, `*.json`, or
all certificate extensions could conceal shareable project files without
repository evidence.

## Decision: Make the Django secret environment-provided

Replace the committed development value in `./config/settings.py` with a
required environment lookup for `SECRET_KEY`. Define the expected local setup
in the validation guide and add focused regression coverage for present and
missing values. The already committed value must be rotated/revoked separately
by a human/deployment owner.

**Rationale:** Ignoring future secret files does not remediate a secret already
in source control. Django must fail closed when no non-empty key is supplied;
Git ignore rules cannot remove historical commits or rotate a deployed key.

**Alternatives considered:** Keeping a fallback development key defeats the
secret-remediation clarification; automatic rotation in application startup is
unsafe and cannot revoke copies in Git history or deployed systems.

## Decision: Validate with Git's diagnostic commands

Use `git check-ignore -v --no-index` for representative paths and verify the
safe `.env.example` is not ignored. Use `git ls-files` and `git status` to
confirm no sensitive fixtures are tracked or added. Run the Django test suite
with a non-empty `SECRET_KEY` supplied by the test environment.

**Rationale:** `check-ignore -v` identifies both the rule and source file,
directly proving the acceptance criteria without committing artifact fixtures.
