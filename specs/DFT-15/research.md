# DFT-15 Research

## Repository and integration patterns

**Decision:** Reuse Django 5.2's email-based custom `User`, session
authentication, class-based views, CSRF-protected forms, and account URL
surface. Put state transitions in an `accounts` service layer and use
`transaction.atomic` for one-time operations.

**Rationale:** `./accounts/models.py`, `./accounts/views.py`, and
`./accounts/urls.py` already own login, profile, and activity behavior. The
checklist services demonstrate the repository's preferred authorization and
transaction pattern. Replacing Django authentication would risk breaking
unenrolled accounts and existing sessions.

**Alternatives considered:** A separate authentication app or middleware-only
MFA layer would duplicate the existing account flow.

## TOTP and provisioning

**Decision:** Use RFC 6238-compatible, six-digit, 30-second TOTP with a
documented one-step clock-skew policy and an account-bound pending enrollment
record. Generate an `otpauth://` provisioning value for an authenticator app;
QR image generation is out of scope because the repository has no QR dependency.

**Rationale:** The specification approves authenticator-app TOTP and forbids
SMS/email delivery. Standard-library implementation avoids an unapproved
runtime dependency, while the pending record prevents interrupted enrollment
from enabling login.

**Alternatives considered:** `django-otp`/`pyotp` plus a QR package would add
novel runtime dependencies. WebAuthn, SMS, email OTP, and remembered browsers
are outside scope.

## Secret and backup-code handling

**Decision:** Store the TOTP seed only through a human-approved deployment
secret-at-rest mechanism; never log or expose it after enrollment. Generate a
fixed set of random backup codes at enrollment, persist only password-style
hashes, display the plaintext set once, consume each atomically, and invalidate
remaining hashes on regeneration or factor replacement.

**Rationale:** This is the approved backup-code policy. The repository has no
encryption key management, so the security owner must approve/provision the
secret-at-rest mechanism before implementation.

**Alternatives considered:** Plaintext seed/code storage and hashing the TOTP
seed were rejected; the former leaks secrets and the latter cannot verify TOTP.

## Rate limiting and fail-closed behavior

**Decision:** Add an atomic, account/login-transaction-bound throttle for
password-factor and TOTP submissions, with expiry and generic errors. Protected
login remains incomplete until the factor succeeds; service errors fail closed.

**Rationale:** Repository inspection found no existing login throttle, lockout,
cache configuration, or recovery-token flow despite the specification's
assumption. A bounded database record is the smallest dependency-free design;
limits and retention require security-owner review.

**Alternatives considered:** `ActivityLog` counters and a new cache or third-
party rate-limit package were rejected for lack of atomic/approved support.

## Recovery and audit governance

**Decision:** Model recovery as a support-mediated state transition: the
requester verifies control of the account email, then an authorized support
operator records the manual identity check and completes reset, replacement, or
disablement. Extend `ActivityLog` for enrollment, verification success/failure,
recovery, replacement, disablement, and backup-code events without secrets.

**Rationale:** This follows the approved clarification and matches the
repository's only audit mechanism. The current `./SECURITY_ZONES.md` lists
placeholder `src/*` paths, so humans must correct it and mirror actual
`accounts` and sensitive-template paths into factory configuration before any
implementation work.

**Alternatives considered:** Password-only disablement, email-only reset,
self-service recovery, and a new audit subsystem were rejected.
