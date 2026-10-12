# Feature Specification: Repository Ignore Rules for Database, Uploads, and Secrets

**Feature Branch**: `DFT-20-add-gitignore`

**Created**: 2026-10-12

**Status**: Draft

**Input**: User description: "Add a .gitignore so the database, uploads, and secrets stay out of the repo"

## Clarifications

### Session 2026-10-12

- Q: The ticket says secrets should stay out of the repository, but ./config/settings.py currently commits a development SECRET_KEY. Should DFT-20 remain ignore-only, or also move that setting to an environment-provided value and handle rotation/removal of the committed key? → A: Include secret remediation: load SECRET_KEY from the environment, remove the committed value, and address rotation separately as part of this change.
- Q: Which SQLite artifacts should the root .gitignore cover for the database configured at ./db.sqlite3? → A: /db.sqlite3, /db.sqlite3-shm, /db.sqlite3-wal, and /db.sqlite3-journal
- Q: Which repository-local upload directories must be ignored, given that PRIVATE_DOCUMENT_ROOT defaults to ./private_documents but can be overridden to a location outside the repository? → A: /private_documents/ only, including all nested content; an overridden external PRIVATE_DOCUMENT_ROOT needs no repository rule
- Q: What exact local secret and credential filename patterns should be ignored, and which safe configuration examples, if any, must remain trackable? → A: Ignore .env and .env.* except .env.example, plus only explicitly named local credential files; no example file currently exists in the repository

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep local database artifacts untracked (Priority: P1)

As a developer running the project locally, I want generated database files and related local database artifacts ignored so they do not appear as repository changes or get committed accidentally.

**Why this priority**: Local database contents can contain application data and should be excluded from version control as the primary protection requested by the ticket.

**Independent Test**: Create representative local database artifacts at the repository's database locations, inspect repository status, and confirm they are ignored without changing tracked source files.

**Acceptance Scenarios**:

1. **Given** a repository checkout with the new ignore rules, **When** a developer creates a local database file using the supported database filename or location, **Then** version-control status does not report that file as an untracked change.
2. **Given** a database artifact is covered by an ignore rule, **When** the developer checks the ignore decision, **Then** the matching rule can be identified and the artifact remains absent from normal repository change lists.

---

### User Story 2 - Keep uploaded files untracked (Priority: P1)

As a developer or local application operator, I want runtime-uploaded files ignored so user-provided content is not added to the repository.

**Why this priority**: Uploads may contain private or user-generated data and can grow or change during normal operation; excluding them prevents accidental repository exposure and noise.

**Independent Test**: Place representative files and nested directories under the application's upload storage locations, inspect repository status, and confirm they are ignored.

**Acceptance Scenarios**:

1. **Given** an upload directory exists in a repository checkout, **When** a file is added at its root or in a nested upload directory, **Then** the file is ignored by version control.

---

### User Story 3 - Keep local secrets untracked (Priority: P1)

As a developer configuring the project locally, I want secret-bearing environment and credential files ignored so credentials are not committed to the repository.

**Why this priority**: Preventing secret disclosure is a security requirement and is explicitly included in the ticket.

**Independent Test**: Create representative local environment and secret files, inspect repository status, and confirm they are ignored while a safe configuration template, if present, remains eligible for version control.

**Acceptance Scenarios**:

1. **Given** a developer creates a local secret-bearing configuration file matching the supported environment or credential naming convention, **When** repository status is inspected, **Then** the file is ignored.
2. **Given** a non-secret configuration example is intentionally tracked, **When** the ignore rules are evaluated, **Then** the example is not unintentionally excluded from version control.

---

### Edge Cases

- What happens when a database, upload, or secret file is nested below its expected directory? It must remain ignored wherever the rule is intended to cover nested artifacts.
- How does the system handle an already tracked database, upload, or secret file? Ignore rules do not remove or untrack existing files; the change must not imply that cleanup of tracked content is included.
- What happens when an ignore pattern could also match a safe configuration template? The rules should exclude secret-bearing local files without excluding intentionally shareable examples.
- What happens when an expected database or upload location is empty? The ignore rules may keep the directory absent from version control; no placeholder directory is required unless separately specified.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The repository MUST contain a root-level `.gitignore` file.
- **FR-002**: The `.gitignore` MUST ignore generated local database files and database-related runtime artifacts covered by the project's supported local database naming or location conventions.
- **FR-003**: The `.gitignore` MUST ignore files and nested content generated in the project's upload storage locations.
- **FR-004**: The `.gitignore` MUST ignore local secret-bearing environment, credential, and equivalent configuration files covered by the project's supported naming conventions.
- **FR-005**: The ignore rules MUST prevent newly created matching files from appearing as untracked repository changes.
- **FR-006**: The ignore rules MUST NOT remove, modify, or untrack files that are already committed.
- **FR-007**: The ignore rules SHOULD preserve intentionally shareable configuration examples when their names distinguish them from local secrets.
- **FR-008**: The feature MUST be limited to adding ignore configuration and documentation needed to explain ambiguous rules; it MUST NOT write database, upload, or secret content into the repository.
- **FR-009**: The change MUST respect declared security zones and MUST NOT plan writes inside a `payments`, `auth`, or `pii` security zone.

### Key Entities *(include if feature involves data)*

- **Ignore rule set**: The root-level collection of version-control patterns that identifies generated database artifacts, upload content, and local secrets.
- **Local artifact**: A generated database file, uploaded file, or secret-bearing configuration file present in a developer or runtime checkout and intended to remain outside version control.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of representative database artifact fixtures created at each documented supported location are reported as ignored.
- **SC-002**: 100% of representative upload files, including files in nested directories, are reported as ignored.
- **SC-003**: 100% of representative local secret and credential files are reported as ignored, while each explicitly supported safe configuration example remains eligible to be tracked.
- **SC-004**: The repository contains exactly one root-level `.gitignore` added by this feature, and no database, upload, or secret content is added to version control.

## Assumptions

- The repository uses Git, and the requested `.gitignore` is intended to be at the repository root.
- Exact database filenames, upload directory names, and secret-file naming conventions were not provided. **MISSING INPUT**: confirm the project's supported paths and names; the implementation should cover the confirmed conventions and document any intentionally excluded variants.
- Common local forms such as database files, an uploads directory, environment files, and credential files are reasonable initial categories, but no specific extension or directory is asserted without confirmation.
- A safe configuration example may exist, but its filename and location were not provided. **MISSING INPUT**: identify any example or template files that must remain trackable and ensure the rules do not exclude them.
- Existing tracked sensitive files, if any, require a separate human-reviewed cleanup decision; this feature only adds ignore behavior for newly untracked matching files.
- No database, upload, or secret data is required as a repository fixture; representative test files can be created temporarily outside the committed source tree or removed after verification.
- The change will be delivered through the constitutionally required pull request to protected `main`, with human review and CI required before merge.
- This specification is part of the complete Spec-Kit pipeline; clarification is required if the missing path conventions affect the final rule set.
