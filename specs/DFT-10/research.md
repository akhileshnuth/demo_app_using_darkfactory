# Research: DFT-10 Real Test Coverage

## Decision: Reuse Django's test runner and add coverage.py as an approved test dependency

The repository uses Django 5.2, `django.test.TestCase`, `tests/test_*.py`, and
`python manage.py test`. The specification's authoritative command remains:

```text
coverage run --source=accounts,dashboard,checklists,vault python manage.py test && coverage report
```

`coverage.py` is not declared in `requirements.txt`, and no coverage
configuration or Python CI workflow exists. Because the constitution forbids
novel dependencies without human approval, implementation must obtain approval
before adding `coverage` to the dependency set. The implementation must fail
the workflow if either command fails; no percentage threshold is introduced.

**Alternatives considered:** pytest/pytest-django (unnecessary migration from
the established runner); Django's test runner without coverage (does not meet
FR-006); a coverage percentage gate (explicitly rejected by the clarification).

## Decision: Test through Django's request and management-command boundaries

Use Django `TestCase`/test client tests for rendered routes, redirects,
authorization, database state, and messages. Use direct service tests where the
authorization and emergency-access state transitions are the contract. Use
`override_settings` and Django's locmem email backend for reminder-command
tests, and deterministic database fixtures for all tests. Do not call live SMTP,
filesystem document storage, or other external services.

**Rationale:** This covers user-visible behavior and component boundaries while
matching the existing test convention and keeping test order independent.

## Decision: Scope coverage to currently wired behavior, while recording broken
vault surfaces as assumptions

The wired application surfaces are accounts/profile/activity, dashboard,
checklists/sharing/emergency/notifications, and vault document listing/export,
plus the expiry reminder command. Vault templates reference unwired CRUD names
and `ExportView` references model fields that do not exist. Tests must verify
the behavior that is actually exposed and record any expected behavior for
unwired or ambiguous paths as an assumption rather than silently changing
application code. The plan must not fix those application inconsistencies.

**Alternatives considered:** testing every template link as if it were a public
route (would invent unsupported behavior); excluding vault export (would omit a
wired user-visible flow).

## Decision: Treat actual Django identity, authorization, and document paths as
sensitive for fixture review

`SECURITY_ZONES.md` still contains generic `src/auth`, `src/payments`, and
`src/customers` placeholders, while the actual sensitive surfaces are
`accounts/`, checklist access-control code/models, and vault models/views and
reminder command. Implementation must reconcile the repository and factory zone
map with a human before changing protected declarations. Tests must use the
test database, in-memory email, and temporary resources outside declared zones;
they must not use production `db.sqlite3` or real personal data.

## Decision: Add review-visible quality workflow and documentation

Add a Python quality workflow alongside the existing Node overlay workflow,
with coverage artifact/report publication configured to run even when tests
fail, so failures remain review-visible. Document setup, the authoritative
command, repeat-run expectations, baseline reporting, and dependency approval
in the feature quickstart and repository test documentation selected during
implementation.

**Rationale:** There is currently no root Python CI workflow, and prior ticket
feedback identified missing artifacts on failed test runs as a delivery risk.

## Repository inventory used by the plan

- Entry/config: `manage.py`, `config/settings.py`, `config/urls.py`.
- Accounts: `accounts/models.py`, `forms.py`, `validators.py`, `views.py`,
  `urls.py`.
- Dashboard: `dashboard/views.py`, `urls.py`.
- Checklists: `checklists/models.py`, `forms.py`, `services.py`, `views.py`,
  `urls.py`, `context_processors.py`.
- Vault: `vault/models.py`, `forms.py`, `views.py`, `mixins.py`, `urls.py`,
  `management/commands/send_expiry_reminders.py`.
- Existing tests: `tests/test_dft7.py` and
  `tests/test_document_pagination.py`.
- Existing dependency declaration: `requirements.txt` contains Django only.
- No root `.github/` workflow or Python coverage configuration was found.
