# Quickstart: Validate deployment-ready settings

## Prerequisites

Install the repository's Django 5.2 dependency, run from the repository root,
and use disposable values only. Do not use real credentials.

## Development

Set `DJANGO_ENV=development`, leave production variables unset, and run:

```text
python manage.py check
```

Expected: settings load with the existing SQLite database and do not infer any
production secret.

## Production success

Provide all required values from
`./specs/DFT-18/contracts/deployment-configuration.md`, including an installed
compatible database backend, then run:

```text
DJANGO_ENV=production python manage.py check --deploy
```

Expected: startup succeeds, `DEBUG` is false, injected hosts/origins/database
values are active, and proxy/cookie/HSTS settings match the declared topology.

## Failure and redaction

Repeat with required variables absent, blank, or malformed: empty/wildcard hosts
or origins, invalid booleans/ports, SQLite in production, and simultaneous
TLS/SSL. Expected: startup fails before serving, identifies the offending name
and constraint, and contains none of the test secret, password, DSN, or full
environment.

## Required implementation tests

Add Django tests for production success, missing/invalid values, repeated loads,
secret redaction, approved/rejected host and origin lists, proxy/TLS safeguards,
development SQLite preservation, and conditional SMTP/private-storage checks.
Preserve existing `locmem`, temporary database, `MEDIA_ROOT`, and timezone
overrides. This plan creates no tests.
