# Feature Specification: Deployment-ready application settings

**Feature Branch**: `DFT-18-settings-deployment-ready`

**Created**: 2026-10-12

**Status**: Draft

**Input**: User description: "DFT-18: Get settings.py ready for a real deployment"

## Clarifications

### Session 2026-10-12

- Q: Which deployment platform and configuration contract should `settings.py` support, including the authoritative runtime source, canonical variable names, and secret/non-secret values? → A: Use deployment-injected environment variables for non-secrets and platform-managed secrets injected at runtime, then document the exact names and required values in the deployment configuration documentation.
- Q: What canonical setting selects configuration mode, and which exact values are supported? → A: Use an explicit `DJANGO_ENV` selector with `development` and `production` values, with no fallback from missing production configuration to development behavior.
- Q: What database backend and connection configuration must production use, and may SQLite remain available only for explicitly selected development mode? → A: Require the deployment to provide the production database backend and connection settings, while retaining the current SQLite configuration only for explicit development mode.
- Q: What exact production hostnames, browser origins, reverse-proxy behavior, and TLS-termination arrangement should the settings validate and trust? → A: Require operators to provide the exact public HTTPS hosts and origins and explicitly declare the trusted proxy/TLS arrangement; reject empty or wildcard production restrictions.
- Q: Which HTTPS-related production safeguards are required when TLS terminates at the deployment proxy, including redirect, secure-cookie, HSTS, and forwarded-protocol settings? → A: When the declared topology is HTTPS, enable secure session and CSRF cookies, trusted forwarded-protocol handling, HTTPS redirects, and HSTS according to the operator's approved rollout policy.
- Q: Which existing settings are mandatory in production versus allowed to retain safe defaults, particularly email delivery, private document storage, upload limits, and application URLs? → A: Require every value that affects security, persistence, externally visible URLs, or production operations; allow only documented non-sensitive defaults, and fail startup for missing SMTP or storage settings when the corresponding feature is enabled.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run with production-safe defaults (Priority: P1)

As a deployment operator, I want the application settings to select safe production behavior so that a real deployment does not accidentally run in development mode or expose diagnostic details.

**Why this priority**: Unsafe defaults can expose secrets and internal information or cause an otherwise valid deployment to run incorrectly. This is the minimum value of making the settings deployment-ready.

**Independent Test**: Can be tested by loading the settings with a production environment and verifying that development-only behavior is disabled, required production configuration is enforced, and the application reports configuration errors before serving requests.

**Acceptance Scenarios**:

1. **Given** a production environment with all required configuration supplied, **When** the settings are loaded, **Then** production-safe behavior is selected and initialization succeeds.
2. **Given** a production environment with a required setting missing or invalid, **When** the settings are loaded, **Then** initialization fails clearly rather than starting with an unsafe fallback.

---

### User Story 2 - Supply deployment configuration externally (Priority: P2)

As a deployment operator, I want environment-specific settings to come from the deployment environment so that the same application artifact can be promoted without editing source files or embedding secrets.

**Why this priority**: Externalized configuration is necessary for repeatable deployments and prevents credentials and environment-specific values from being committed to the repository.

**Independent Test**: Can be tested by loading the settings twice with two different sets of deployment-provided values and verifying that the resulting configuration changes accordingly without changing the application artifact.

**Acceptance Scenarios**:

1. **Given** deployment configuration supplied through the supported external configuration mechanism, **When** the settings are loaded, **Then** the supplied values are used for the corresponding runtime configuration.
2. **Given** a secret value supplied by the deployment environment, **When** configuration loading or validation reports an error, **Then** the secret value is not included in the error or diagnostic output.

---

### User Story 3 - Restrict production access and origins (Priority: P3)

As a deployment operator, I want production host and origin controls to be explicit so that the deployed application accepts traffic only from approved locations.

**Why this priority**: Explicit boundary configuration reduces exposure when the application is reachable from a real network, while remaining independently verifiable after the baseline production settings work.

**Independent Test**: Can be tested by loading an approved host/origin configuration, confirming approved requests are accepted, and confirming unapproved values are rejected or denied according to the application’s existing behavior.

**Acceptance Scenarios**:

1. **Given** an approved host and origin configuration, **When** the settings are loaded, **Then** those approved values are available to the application’s request and origin checks.
2. **Given** an empty, wildcard, malformed, or otherwise unsafe production host/origin configuration, **When** the settings are validated, **Then** validation fails or applies the documented safe restriction rather than allowing unrestricted access.

---

### Edge Cases

- When a required deployment variable is absent, blank, malformed, or has the wrong type, configuration loading must fail with an actionable message that identifies the setting without revealing secret contents.
- When boolean, list, URL, host, port, or numeric values contain surrounding whitespace or unexpected formatting, validation must either normalize the value consistently or reject it clearly; it must not silently choose an unsafe value.
- When a production deployment omits an allowed-host or allowed-origin restriction, the settings must not silently fall back to unrestricted access.
- When a deployment supplies a development-only flag enabled, production loading must reject it or enforce the production-safe value.
- When configuration is loaded more than once in the same process, the result must remain consistent for the same environment and must not expose secret values through representations or diagnostics.
- When an existing local-development workflow does not provide production-only variables, it must remain usable only if the existing development mode is explicitly selected; production mode must not infer development mode from missing deployment configuration.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST distinguish explicitly between development and production configuration modes.
- **FR-002**: System MUST use production-safe defaults for diagnostic, debug, and error-display behavior when production mode is selected.
- **FR-003**: System MUST obtain deployment-specific configuration from an external runtime configuration source rather than requiring environment-specific values to be committed in source code.
- **FR-004**: System MUST require and validate every configuration value necessary for a production deployment before the application serves traffic.
- **FR-005**: System MUST validate configuration types, formats, and allowed values and MUST report invalid configuration as a startup failure.
- **FR-006**: System MUST prevent secret values from appearing in configuration errors, diagnostics, or other settings representations.
- **FR-007**: System MUST make production host and origin restrictions explicit and MUST not silently permit unrestricted access when required restrictions are absent.
- **FR-008**: System MUST preserve an explicitly selected development configuration path for local use without allowing missing production configuration to select it implicitly.
- **FR-009**: System MUST document each required deployment setting, its expected form, and whether it is secret or non-secret in the feature’s deployment-facing configuration documentation.
- **FR-010**: Any functional implementation work resulting from this specification MUST include automated tests for successful production loading, missing or invalid required values, secret redaction, and host/origin restrictions.
- **FR-011**: Any change to a path declared by the repository or factory as an auth, payments, or PII security zone MUST be excluded from autonomous implementation and handled through the required human-gated process.
- **FR-012**: The feature MUST NOT introduce a new runtime dependency without human approval.

### Key Entities *(include if feature involves data)*

- **Deployment configuration**: The non-secret and secret values supplied by an execution environment to control application behavior for a deployment.
- **Configuration mode**: The explicitly selected development or production context that determines defaults, validation strictness, and operational safeguards.
- **Allowed origin and host policy**: The approved network locations from which the deployed application may accept requests.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of production configuration loads with a missing or invalid required value fail before the application serves requests.
- **SC-002**: 100% of production configuration loads use the production-safe diagnostic and debug behavior, with no development fallback caused solely by missing production values.
- **SC-003**: 100% of automated configuration tests that exercise errors or diagnostics contain no raw secret values in their captured output.
- **SC-004**: Every production deployment configuration item is documented with its requiredness, accepted form, and secret status before implementation is considered complete.
- **SC-005**: A deployment operator can use one unchanged application artifact in at least two explicitly configured environments by changing runtime configuration only.

## Assumptions

- The ticket’s reference to `settings.py` means the application’s central runtime configuration module, but the current contents and framework are a **MISSING INPUT**; the implementation plan must first map these requirements to the existing settings structure without changing unrelated behavior.
- The deployment platform, supported configuration mechanism, canonical variable names, required production values, and approved host/origin values are **MISSING INPUTS**; these must be confirmed before implementation and documented rather than invented as externally visible API names.
- The intended production deployment topology, reverse-proxy behavior, and TLS termination arrangement are **MISSING INPUTS**; host, origin, URL, and security settings must be finalized against that topology.
- No design file, wiki page, linked document, or deployment runbook was provided. Such material is a **MISSING INPUT** and is not required to define the configuration-safety behavior above, but any project-specific values in it must be reconciled during clarification.
- Existing application behavior and local-development defaults are assumed to remain compatible unless explicitly overridden by an approved production configuration.
- Secrets are assumed to be supplied by an approved runtime secret mechanism and are not to be committed to the repository, logged, or echoed in diagnostics.
- This specification does not authorize autonomous writes inside declared security zones; the repository and factory zone-map declarations must be checked during clarification, and any zoned settings change requires human handling.
- The feature is limited to deployment configuration readiness. Infrastructure provisioning, release automation, credential rotation, and changes to authentication, payments, or PII workflows are out of scope unless separately specified.
