# DFT-15 Web Contracts

These are server-rendered Django form contracts following the existing
`accounts` URL naming convention.

## Authenticated account-security routes

- `GET /profile/security/`: show enabled state and available actions.
- `POST /profile/security/enroll/`: authenticated only; create a time-limited
  enrollment and show the one-time provisioning value.
- `POST /profile/security/enroll/verify/`: verify the pending TOTP; on success
  enable the factor and show backup codes once.
- `POST /profile/security/disable/` and `/replace/`: create recovery requests;
  never change factor state directly.

All forms require CSRF protection, generic errors, user scoping, and throttling.

## Login routes

- Existing `POST /accounts/login/`: retain password-only success when disabled;
  when enabled, establish only a pending login transaction.
- `GET/POST /accounts/login/verify/`: accept a TOTP or one backup code for the
  exact pending transaction; only success completes the Django session.

No trusted-browser cookie or challenge bypass is issued.

## Recovery/support routes

- `POST /profile/security/recovery/`: start recovery and send an account-email
  verification action without disclosing account existence.
- Support completion is staff-authorized through the reviewed support/admin
  surface selected by the human owner and requires the manual identity check.

## Response rules

Unknown account, wrong, expired, mismatched, and reused factors receive generic
responses. Secrets, codes, tokens, and provisioning values never appear in
HTML, redirects, messages, audit text, logs, or analytics. Every security
transition emits the corresponding established activity/security event.
