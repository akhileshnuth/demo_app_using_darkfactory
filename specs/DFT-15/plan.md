# Implementation Plan: Two-Factor Login for Extra Account Security

**Branch**: `DFT-15-two-factor-login` | **Date**: 2026-10-12 | **Spec**: `./specs/DFT-15/spec.md`

**Input**: Feature specification from `./specs/DFT-15/spec.md`

## Summary

Add authenticator-app TOTP login, single-use backup codes, enrollment and
factor lifecycle flows, and support-mediated recovery while preserving
password-only login for unenrolled accounts. Wrap Django's existing session
login, use an `accounts` service layer for atomic security transitions, extend
`ActivityLog`, and add no runtime dependency without human approval.

## Technical Context

**Language/Version**: Python 3.11+ / Django 5.2 (repository is running Django 5.2.18)

**Primary Dependencies**: Existing Django stack and Python standard library; no new runtime dependency selected

**Storage**: Existing Django database (SQLite in development); new account-security, enrollment, challenge, backup-code, recovery, and throttle records require migrations

**Testing**: Django `TestCase` via `python manage.py test`, with focused account/security integration coverage

**Target Platform**: Server-rendered Django web application on the existing Linux deployment target; authenticator apps are external clients

**Project Type**: Server-rendered web application

**Performance Goals**: Preserve the existing login path; factor verification and enrollment target p95 <250 ms excluding support/email operations

**Constraints**: Fail closed; never log or display secrets/codes; every login needs a fresh factor; backup codes are hashed and shown once; recovery requires verified account email plus manual support identity review; security-zone writes are human-gated

**Scale/Scope**: One Django accounts surface, existing user/session model, three user journeys (enroll/login/recover), and the existing activity feed; no remembered devices, SMS/email OTP, WebAuthn, or bulk administration

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **PASS with human gate**: Authentication, recovery, migrations, security events, and sensitive templates are security-zone work. Before implementation, a human must reconcile `./SECURITY_ZONES.md` with the real `./accounts/`, `./accounts/migrations/`, `./templates/registration/`, and relevant `./templates/dashboard/` paths and mirror them into factory configuration (`FACTORY_ZONES` or `agentguard/policies/zones/zones-v0.json`). Agents must not write those paths.
- **PASS with human review**: The implementation must ship tests and land through a reviewed PR against protected `main`.
- **PASS**: The design avoids novel runtime dependencies. A TOTP/QR package may not be added unless a human approves the dependency, version, license, and supply-chain review. The initial contract uses an `otpauth://` provisioning value; QR rendering is out of scope.
- **PASS with prerequisite**: The repository has no existing rate limiter or recovery flow. The plan includes an atomic, database-backed factor-attempt throttle and a staff-only support completion transition rather than claiming nonexistent infrastructure.
- **PASS**: Product clarifications are resolved by the approved specification. Secret-at-rest key management must be supplied and approved by the human security owner before implementation.

## Project Structure

### Documentation (this feature)

```text
./specs/DFT-15/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/http.md
```

### Source Code (repository root)

```text
./accounts/
├── models.py
├── forms.py
├── services.py
├── views.py
├── urls.py
└── migrations/
./templates/registration/
./templates/dashboard/
./tests/
```

**Structure Decision**: Extend the existing `accounts` Django app and its
server-rendered templates. Keep cryptographic/state transitions in services,
HTTP concerns in views/forms, and audit display in the existing dashboard
activity surface. Add no separate frontend or authentication subsystem.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| None | N/A | The feature fits the existing single Django project and accounts app. |
