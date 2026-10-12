# DFT-10 validation guide

## Prerequisites

1. Use the repository's supported Python environment.
2. Install the declared Django dependency and, after human approval, the
   `coverage.py` test dependency from the approved requirements file.
3. Run from the repository root. Do not use production `db.sqlite3` or real
   email/document data.

## Authoritative validation

```bash
coverage run --source=accounts,dashboard,checklists,vault python manage.py test && coverage report
```

Expected outcome: Django discovers all `tests/test_*.py` cases, all tests pass,
and `coverage report` prints rows for the four application packages. The command
returns non-zero if tests fail or if coverage cannot produce its report. No
percentage threshold is enforced for DFT-10; record the initial report as the
baseline in the review/CI artifact.

Run the same command twice from a clean test environment. Both runs must have
the same pass/fail result and must not require manual state cleanup.

## CI validation

The implementation should add a Python workflow that installs approved
dependencies, runs the exact command above, and uploads the coverage output or
report with `if: always()` so failed runs remain reviewable. The workflow must
not replace the existing Node overlay workflow.

## Scope references

- User-visible contracts: [contracts/user-visible-flows.md](contracts/user-visible-flows.md)
- Fixture and coverage entities: [data-model.md](data-model.md)
- Security-zone reconciliation: `SECURITY_ZONES.md` and the factory zone map;
  resolve this with human review before implementation writes sensitive paths.
