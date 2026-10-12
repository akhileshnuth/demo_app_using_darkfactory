# Implementation Plan: Add Real Test Coverage Across the App

**Branch**: `DFT-10` | **Date**: 2026-10-12 | **Spec**: `./specs/DFT-10/spec.md`

**Input**: Feature specification from `./specs/DFT-10/spec.md`

## Summary

Expand the existing Django `TestCase` suite to cover all currently wired,
user-visible flows in accounts, dashboard, checklists, and vault, including
authorization, validation, state transitions, and dependency-error paths. Add
controlled fixtures/test doubles, establish the approved coverage.py command,
and add a review-visible Python CI workflow without changing application source
behavior. The initial coverage percentage is reported as a baseline and is not
a failing threshold.

## Technical Context

**Language/Version**: Python version supported by the repository environment;
Django `~=5.2`.

**Primary Dependencies**: Django's built-in test runner and test client;
`coverage.py` is required by the approved command but is not currently declared
and needs human approval before addition.

**Storage**: Django test database (SQLite configuration); locmem email backend
and temporary test-owned resources for dependency isolation. Never use the
development database or production data.

**Testing**: `django.test.TestCase`, `python manage.py test`, and the
authoritative command `coverage run --source=accounts,dashboard,checklists,vault
python manage.py test && coverage report`.

**Target Platform**: Linux CI and local repository environments.

**Project Type**: Django web application with server-rendered user-visible
routes and one management command.

**Performance Goals**: Deterministic suite suitable for repeated local and CI
runs; no new application performance requirement.

**Constraints**: No application behavior changes; no live services or real
PII; no coverage percentage gate; no novel dependency without human approval;
coverage/test failures must return non-zero; tests must avoid declared and
actual sensitive paths.

**Scale/Scope**: All implemented user-visible flows wired under accounts,
dashboard, checklists, and vault, plus `send_expiry_reminders`; existing tests
are retained and expanded rather than replaced.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

- **I. Complete Spec-Kit pipeline**: PASS for this planning phase; this plan
  produces the required Phase 0/1 artifacts and explicitly leaves `tasks.md`
  to the tasks phase.
- **II. Declared security zones**: CONDITIONAL PASS. The repository declaration
  still has generic placeholder paths and does not mirror actual Django
  sensitive surfaces. Implementation must obtain human review and reconcile
  `SECURITY_ZONES.md` with the factory zone map before protected-path changes;
  test fixtures themselves use isolated DB/memory/temp resources.
- **III. Human-gated merge**: PASS. CI/workflow changes are intended for a PR
  and human merge; no direct merge is part of this plan.
- **IV. Test-first**: PASS. This feature is test coverage and adds tests for all
  planned behavior without changing application source behavior.
- **V. No novel dependencies**: CONDITIONAL PASS. `coverage.py` is required by
  the approved specification but absent from requirements; human approval is a
  prerequisite to adding it. If approval is withheld, implementation must
  stop rather than silently substitute a different coverage tool.

No unjustified constitution violation is accepted. The two conditional gates
are explicit human/implementation prerequisites, not waivers.

## Project Structure

### Documentation (this feature)

```text
./specs/DFT-10/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── user-visible-flows.md
```

### Source and test areas to change in implementation

```text
./accounts/                       # inspect only; behavior must not change
./dashboard/                      # inspect only; behavior must not change
./checklists/                     # inspect only; behavior must not change
./vault/                          # inspect only; behavior must not change
./tests/
├── test_dft7.py                  # retain and extend only where appropriate
├── test_document_pagination.py   # retain existing vault list coverage
├── test_accounts.py              # add account/form/profile/activity cases
├── test_dashboard.py             # add authenticated/anonymous shell cases
├── test_checklists.py            # add CRUD, auth, sharing, emergency, notices
├── test_vault.py                 # add list/export/ownership/error cases
└── test_expiry_reminders.py      # add command/email/failure cases
./requirements.txt                # add approved coverage dependency only
./.github/workflows/python-tests.yml  # add Python quality workflow if approved
./.gitignore                      # ignore coverage data only if required
```

Tests should use shared helper fixtures only in test modules or a clearly named
test-support module, and must not modify `accounts/`, `dashboard/`,
`checklists/`, or `vault/` application behavior. The CI workflow must upload
reports/artifacts with `if: always()` while preserving the command's failure
status.

**Structure Decision**: Keep the repository's flat Django apps and `./tests/`
suite. Add focused modules matching the existing convention rather than
introducing pytest or a new application layer.

## Planned coverage slices

1. **Accounts/dashboard:** signup success and validation failures, password
   strength/duplicate email, login activity, protected redirects, profile
   ownership, activity pagination/scoping, and dashboard navigation.
2. **Checklists:** owner CRUD and item mutations, invalid forms, owner-only
   authorization, shared read access, share/revoke notifications and activity,
   emergency request/approve/deny/expiry/removal transitions, and recipient-
   scoped notification actions.
3. **Vault:** owner-scoped list/search/filter/pagination and anonymous denial;
   export's supported response and controlled failure behavior; form ownership
   and duplicate validation; expiry reminder selection, idempotence, locmem
   delivery, and send failure handling.
4. **Workflow:** exact documented command, repeatability, baseline report, and
   non-zero propagation for test or coverage-report failures.

## Implementation notes and assumptions

- Preserve the current application behavior as the oracle. For broken/unwired
  vault template links and export fields absent from `Document`, record an
  assumption or expected failure in tests/design review; do not repair source
  code under DFT-10.
- Use `override_settings` for email/configuration and mock only external
  dependency boundaries, not the behavior under test.
- Verify test isolation by running the suite twice and, where practical, with
  randomized/order-independent execution supported by Django's runner.
- Reconcile actual sensitive paths (`accounts/`, checklist access-control
  surfaces, vault document metadata/reminder code) with the factory map through
  the human-gated security process; do not assume the placeholder rows are
  authoritative.

## Complexity Tracking

No constitution violations are being accepted or waived. The only conditional
items are the required human approval for `coverage.py` and security-zone map
reconciliation, both mandated by the constitution/specification.
