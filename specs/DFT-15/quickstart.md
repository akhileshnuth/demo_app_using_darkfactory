# DFT-15 Validation Quickstart

This is a validation guide for implementation, not an implementation or test
suite.

## Prerequisites

1. Obtain human approval for secret-at-rest handling and factor-attempt limits.
2. Reconcile `./SECURITY_ZONES.md` and factory zone mappings.
3. Install dependencies and apply migrations:

```text
python -m pip install -r requirements.txt
python manage.py migrate
```

## Automated validation

```text
python manage.py test
```

Coverage should exercise `./specs/DFT-15/data-model.md` and
`./specs/DFT-15/contracts/http.md`: enrollment, every-login challenge,
single-use backup codes, invalid/expired/replayed/mismatched responses,
throttling, generic errors, recovery authorization, and activity isolation.

## Manual end-to-end scenarios

1. Confirm an unenrolled account logs in without a factor prompt.
2. Enroll with an authenticator-app TOTP, confirm enablement, and verify backup
   codes are displayed once.
3. Log out and confirm password authentication alone does not grant access;
   valid TOTP completes login, while invalid, expired, replayed, and
   cross-transaction codes fail.
4. Redeem one backup code, retry it, regenerate codes, and confirm old codes
   are invalidated.
5. Attempt disable/replace/recovery without both identity checks; confirm the
   factor remains enabled. Complete reviewed support recovery and verify the
   requested transition and audit event.
6. Inspect the authorized activity view and confirm required events exist with
   no secret, code, or recovery token present.
