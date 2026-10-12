# Feature Specification: Two-Factor Login for Extra Account Security

**Feature Branch**: `DFT-15-two-factor-login`

**Created**: 2026-10-12

**Status**: Draft

**Input**: User description: "Ticket DFT-15: Add two-factor login for extra account security"

## Clarifications

### Session 2026-10-12

- Q: Which second-factor method and delivery mechanism should the initial release implement? → A: TOTP codes from an authenticator app, with no SMS or email delivery
- Q: What exact identity-verification process and authority should handle a user who loses the factor or wants to disable or replace it? → A: A support-mediated recovery flow requiring verified control of the account email plus a manual identity check before reset
- Q: After a successful second-factor challenge, should the system remember a trusted browser or require a challenge again on every new login? → A: Require the second factor for every login and browser session
- Q: Are one-time backup or recovery codes required in the initial two-factor release, and if so what generation, storage, and regeneration policy should they use? → A: Yes: generate a fixed set of single-use codes at enrollment, store only hashes, show them once, and invalidate the remaining set on regeneration or factor replacement

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Enable two-factor login (Priority: P1)

As an authenticated account holder, I want to enable two-factor login so that a password alone is not sufficient to access my account.

**Why this priority**: Account protection is the primary value of the feature; users must be able to enroll before two-factor verification can protect subsequent logins.

**Independent Test**: An authenticated test account can enable two-factor login, complete the required verification, and confirm that the account reports two-factor login as enabled.

**Acceptance Scenarios**:

1. **Given** an authenticated account with two-factor login disabled, **When** the account holder starts enrollment and completes the presented second-factor verification, **Then** two-factor login is enabled for that account.
2. **Given** an enrollment attempt with an invalid or expired second-factor response, **When** the account holder submits it, **Then** enrollment is not completed and the account remains protected by its prior login configuration.

---

### User Story 2 - Complete a two-factor login (Priority: P1)

As a user with two-factor login enabled, I want to provide a valid second factor after my password so that I can securely access my account.

**Why this priority**: Enrolled users need a reliable login journey, and requiring the second factor is the central security behavior of the feature.

**Independent Test**: A test account with two-factor login enabled can log in with valid primary credentials and a valid second factor, and is denied access when the second factor is invalid.

**Acceptance Scenarios**:

1. **Given** an account with two-factor login enabled and valid primary credentials, **When** the user provides a valid second factor, **Then** login completes and the user receives access to the account.
2. **Given** an account with two-factor login enabled and valid primary credentials, **When** the user provides an invalid, expired, or missing second factor, **Then** login does not complete and the user receives a clear retry or recovery path without account access.
3. **Given** an account with two-factor login disabled, **When** the user logs in with valid primary credentials, **Then** the existing login flow remains available without an unnecessary second-factor challenge.

---

### User Story 3 - Recover or disable two-factor login (Priority: P2)

As an account holder who cannot use the configured second factor, I want a secure recovery or disablement process so that I can regain access without weakening protection for other accounts.

**Why this priority**: Loss of the second-factor method is an expected account-support scenario; a defined path prevents avoidable lockout while preserving account security.

**Independent Test**: A test account unable to provide its second factor can follow the approved recovery path, while an unauthenticated or insufficiently verified requester cannot disable two-factor login.

**Acceptance Scenarios**:

1. **Given** an account with two-factor login enabled and an account holder who cannot provide the second factor, **When** the holder completes the approved recovery process, **Then** access is restored or two-factor login is changed only after the required identity verification succeeds.
2. **Given** an account with two-factor login enabled, **When** a requester attempts to disable it without the required authenticated verification, **Then** the request is rejected and two-factor login remains enabled.

---

### Edge Cases

- If a second-factor response is expired, malformed, already used, or otherwise invalid, the system must reject it without granting access or completing enrollment.
- If a user submits repeated invalid second factors, the system must apply the existing account-protection and rate-limiting policies and must not disclose whether a credential or factor was close to valid.
- If enrollment is abandoned or interrupted before verification succeeds, two-factor login must remain disabled and incomplete enrollment data must not be usable for login.
- If the user has multiple login attempts or browser sessions in progress, a second-factor response must not be accepted for a different account or login transaction.
- If the configured second-factor service or delivery mechanism is unavailable, the system must fail closed for protected login and provide the approved recovery or retry path.
- If a user changes or loses access to the configured second-factor method, the system must require the approved identity-verification process before replacement or disablement.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow an authenticated account holder to start two-factor login enrollment.
- **FR-002**: System MUST require successful verification of the second factor before marking enrollment complete.
- **FR-003**: System MUST persist whether two-factor login is enabled for each account and MUST apply that setting to subsequent login attempts.
- **FR-004**: System MUST require a valid second factor after valid primary credentials for every login to an account with two-factor login enabled.
- **FR-005**: System MUST deny account access when the required second factor is missing, invalid, expired, already used, or associated with another account or login transaction.
- **FR-006**: System MUST avoid revealing sensitive account or factor-validation details in errors, prompts, and recovery responses.
- **FR-007**: System MUST protect enrollment, verification, replacement, recovery, and disablement operations with appropriate authentication and authorization checks.
- **FR-008**: System MUST provide the approved recovery path for an account holder who cannot use the configured second factor.
- **FR-009**: System MUST allow two-factor login to be disabled or its factor to be replaced only after the required authenticated identity verification succeeds.
- **FR-010**: System MUST record security-relevant enrollment, successful verification, failed verification, recovery, replacement, and disablement events using the repository's established security-event handling.
- **FR-011**: System MUST enforce the repository's existing protections against automated repeated login and verification attempts.
- **FR-012**: System MUST preserve the existing login behavior for accounts that have not enabled two-factor login.
- **FR-013**: Any implementation change to authentication or other declared security-zone paths MUST be performed through the human-gated workflow required by the project constitution; this specification does not authorize agent writes in those zones.

### Key Entities *(include if feature involves data)*

- **Account security settings**: The account-level state indicating whether two-factor login is enabled and which approved factor or recovery state is associated with the account.
- **Second-factor enrollment**: A time-bounded, verifiable enrollment attempt linked to one account and used only until enrollment succeeds or expires.
- **Login verification attempt**: A single second-factor challenge and response associated with one account and login transaction, including its validity and expiration state.
- **Security event**: An auditable record of material two-factor enrollment, login verification, recovery, replacement, and disablement activity without storing reusable secret values.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of login attempts for accounts with two-factor login enabled require a valid second factor before account access is granted.
- **SC-002**: 100% of invalid, expired, reused, or mismatched second-factor responses tested in acceptance verification are denied without account access.
- **SC-003**: At least 90% of users with an eligible account can complete two-factor enrollment on their first valid attempt.
- **SC-004**: At least 95% of users with two-factor login enabled can complete a normal login with valid primary credentials and a valid second factor on their first attempt.
- **SC-005**: 100% of tested unauthenticated or insufficiently verified attempts to disable, replace, or recover two-factor login are rejected.
- **SC-006**: All required two-factor security events are available through the existing authorized audit or security-event review process.

## Assumptions

- The existing authentication and account-management flows will be reused rather than replaced.
- The ticket does not specify the second-factor method, delivery mechanism, enrollment UX, recovery mechanism, or factor lifecycle; the product and security owners must select and approve those details before implementation. This is a MISSING INPUT.
- The ticket does not provide a design file, API contract, or existing security-event schema; those materials are MISSING INPUTs if they are required by the implementation, so the implementation must align with the repository's approved existing conventions rather than inventing incompatible ones.
- Users have access to the selected second-factor method during enrollment and normal login.
- Existing password authentication, session handling, rate limiting, audit logging, and account recovery capabilities remain available for integration.
- Mobile-specific behavior, remembered-device behavior, multi-factor methods beyond the approved initial method, and administrative bulk management are unspecified and require product clarification before being treated as requirements. This is a MISSING INPUT.
- Authentication, account recovery, and security-event implementation paths may be declared `auth` or `pii` security zones; no agent is authorized by this specification to write inside those zones, and human-gated changes are required by the constitution.
