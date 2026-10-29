# Data Model: DFT-20 Repository Ignore Rules

This feature has no database schema or application data migration. Its model is
a repository policy and a runtime configuration input.

## Ignore rule set

| Field | Description | Validation / invariant |
|---|---|---|
| Database paths | Root SQLite database and its three runtime sidecars | Exactly the four documented root paths are ignored; unrelated nested SQLite files are not implicitly covered |
| Upload root | `./private_documents/` | Root directory and all descendants are ignored; an external `PRIVATE_DOCUMENT_ROOT` is outside repository scope |
| Environment patterns | `.env` and `.env.*` | `.env.example` remains eligible for tracking |
| Credential patterns | `*.pem`, `*.p12`, `*.key`, `id_rsa*`, `*.private-key*` | Only explicitly named existing patterns are covered; no broad filename/content wildcard is introduced |

## Local artifact

A generated database artifact, uploaded file, or local credential/configuration
file that may exist in a developer checkout but must not become a newly
untracked repository change.

**Rules:**

- Ignore matching newly created artifacts.
- Do not remove, rewrite, or untrack an already committed file.
- Do not add representative sensitive content to the repository.

## Environment secret configuration

`SECRET_KEY` is a required non-empty process environment value consumed by
`./config/settings.py`.

**State transitions:**

1. Developer/deployment supplies `SECRET_KEY` outside source control.
2. Settings import consumes the value.
3. Missing/empty value fails closed rather than selecting a committed fallback.
4. Any historical/deployed key is rotated or revoked through a separate
   human-reviewed operational action.

## Relationships

The upload root corresponds to Django's `PRIVATE_DOCUMENT_ROOT` default and
`MEDIA_ROOT`; no repository rule is needed for an override outside the
checkout. The ignore rule set is independent of Django database schema and
does not alter migrations or persisted application records.
