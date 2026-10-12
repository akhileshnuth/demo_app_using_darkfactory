# Test Data Model: DFT-10

This feature adds verification artifacts, not production entities or schema
changes. Tests use the existing Django models below and create them through
factories/helpers in the test suite only.

## Test Case

- **Fields:** test name, isolated setup inputs, action, expected response/state,
  and cleanup scope.
- **Relationships:** exercises one or more existing application entities and,
  for integration cases, a controlled dependency (email backend or configured
  setting).
- **Validation:** each selected flow has a success case and applicable invalid,
  unauthorized, or dependency-error case; assumptions are documented where the
  existing behavior is ambiguous.

## Test Fixture

- **Fields:** test users, profiles, checklists/items/shares, emergency
  contacts/requests, notifications, document taxonomy/documents, and reminder
  dates.
- **Relationships:** mirror the production foreign-key relationships and
  ownership rules; every fixture is created in Django's isolated test database.
- **Validation:** user-owned querysets cannot expose another user's records;
  duplicate, blank, malformed, self-reference, and invalid state inputs follow
  the existing forms/services behavior.
- **Cleanup:** Django `TestCase` transaction/database teardown removes database
  state. Email uses locmem backend; temporary files, if required by an export
  test, use a test-owned temporary directory and are explicitly removed.

## Coverage Result

- **Fields:** source scope (`accounts`, `dashboard`, `checklists`, `vault`),
  executed test result, report rows, and command exit status.
- **Validation:** `coverage run ... python manage.py test` must pass before
  `coverage report` runs; either test failure or report-generation failure is a
  failing quality result. The initial percentage is reported but not gated.

## Existing application entities exercised

`User`, `Profile`, and `ActivityLog`; `Checklist`, `ChecklistItem`, and
`ChecklistShare`; `EmergencyContact`, `EmergencyAccessRequest`, and
`Notification`; and `Category`, `Subject`, `DocumentType`, and `Document`.
No migrations or application model behavior are part of this plan.
