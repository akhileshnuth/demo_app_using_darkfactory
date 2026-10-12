# DFT-15 Data Model

All records are account-scoped and must not store submitted TOTP values,
plaintext backup codes, or recovery tokens in activity descriptions.

## Account security settings

One-to-one with `accounts.User`: `totp_enabled`, protected `totp_secret`,
`factor_version`, and lifecycle timestamps. State transitions are disabled →
pending enrollment → enabled; enabled → pending replacement → enabled with a
new version; enabled → disabled only through support.

## Second-factor enrollment

An owner-bound, expiring record containing a protected secret reference,
factor version, status (pending/completed/expired/cancelled), and timestamps.
Only pending records can verify; completion and enabling are one transaction.

## Login verification attempt

An account-bound record containing an opaque login transaction ID, factor
version, expiry, attempt count, status (pending/verified/expired/rejected), and
timestamps. A verified or expired transaction cannot be reused.

## Backup code

One row per generated code: user, generation/factor version, `code_hash`,
`used_at`, `invalidated_at`, and creation time. Hashes use the approved
password-hashing primitive; consumption is atomic and single-use.

## Recovery request

An opaque request with user, action (disable/replace/reset), email-verification
state/expiry, support-review state and actor, outcome, and timestamps. Final
transition requires verified email control and an authorized manual identity
check.

## Factor-attempt throttle

Bounded account/transaction/client-attempt state with expiry and atomic
increment. It supports generic rejection and backoff, and is separate from the
audit trail.

## Security event

Reuse `ActivityLog` with new event types. Keep descriptions ≤280 characters and
generic; never include secrets, codes, tokens, or full provisioning values.
