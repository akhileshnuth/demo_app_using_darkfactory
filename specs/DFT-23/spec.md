# Feature Specification: Fix Checklists Crash and Remove Test Files

**Feature Branch**: `DFT-23-fix-checklists-crash`

**Created**: 2026-10-09

**Status**: Draft

**Input**: User description: "Ticket DFT-23: Fix checklists crash (restore missing models) and delete all test files, change nothing else"

## Clarifications

### Session 2026-10-09

- Q: Which missing checklist models should be restored in checklists.models, and should their fields, relationships, constraints, and helper properties match the existing migration and DFT-9 data model exactly? → A: Restore Checklist, ChecklistItem, ChecklistShare, EmergencyContact, EmergencyAccessRequest, and Notification to match checklists/migrations/0001_initial.py and specs/DFT-9/data-model.md exactly.
- Q: Should DFT-23 add a new schema migration after restoring the model classes, or rely on the existing checklists migration that already defines their database schema? → A: Restore the model classes to match the existing migration and do not add a schema migration unless Django detects a genuine schema difference.
- Q: What repository rule should define the files deleted by 'delete all test files'? → A: Delete all tracked files whose path or filename identifies them as tests, including app-level tests.py, tests/**/*.test.js, tests/**/*.test.ts, and overlays/node/tests/**/*.test.ts; retain test-runner configuration and non-test source files.
- Q: Should the implementation add new defensive behavior for missing or unavailable optional checklist relationships, beyond restoring the missing model definitions? → A: No; only restore the missing models and make the minimum changes required to remove the reported crash.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Open Checklists Without a Crash (Priority: P1)

As a user of the checklist functionality, I want the checklists experience to load successfully so that I can access and use checklists without an application crash.

**Why this priority**: Restoring basic checklist functionality is the primary purpose of the ticket and is required before the feature can be considered usable.

**Independent Test**: Can be tested by starting the application in a supported environment, opening the checklists experience, and confirming that it loads without a crash and exposes the expected checklist data or empty state.

**Acceptance Scenarios**:

1. **Given** the application has its checklist dependencies available, **When** a user opens the checklists experience, **Then** the experience loads without a crash.
2. **Given** the checklists experience is opened after the missing models are restored, **When** checklist data is requested, **Then** the data is represented without a missing-model failure and the user receives the normal checklist view or an appropriate empty state.

---

### User Story 2 - Restore the Missing Checklist Models (Priority: P1)

As a maintainer, I want the models required by checklists to be present and consistent with the existing checklist behavior so that the crash-causing missing dependencies are restored without changing unrelated behavior.

**Why this priority**: The ticket identifies missing models as the cause or required remedy for the crash; restoring them is necessary to deliver the primary user outcome.

**Independent Test**: Can be tested by exercising every checklist flow that depends on the restored models and confirming that model resolution and checklist operations complete without missing-model errors.

**Acceptance Scenarios**:

1. **Given** the checklist feature references its required models, **When** those references are resolved, **Then** each required model is available with the attributes and relationships needed by the existing checklist behavior.
2. **Given** the restored models are used by checklist operations, **When** a user views or interacts with a checklist, **Then** the operation completes without the original crash and no unrelated checklist behavior is changed.

---

### User Story 3 - Remove All Test Files (Priority: P2)

As a maintainer, I want all test files removed from the repository so that the repository matches the explicit DFT-23 cleanup requirement.

**Why this priority**: The ticket explicitly requires deletion of all test files, but this cleanup follows the P1 requirement to restore usable checklist behavior.

**Independent Test**: Can be tested by inspecting the repository after the change and confirming that no files classified as test files remain, while the checklist fix and all other requested files remain present.

**Acceptance Scenarios**:

1. **Given** the repository before DFT-23 contains test files, **When** the DFT-23 change is applied, **Then** all files matching the repository's test-file conventions are deleted.
2. **Given** the DFT-23 change is applied, **When** the resulting change set is inspected, **Then** no unrelated source, configuration, documentation, or non-test files are changed.

---

### Edge Cases

- When a checklist has no records, the restored models must allow the normal empty state to load rather than causing a crash.
- When a checklist references a missing, optional, or otherwise unavailable related record, the application must handle the condition without the original missing-model crash and must preserve the existing expected behavior.
- If a file serves both as application source and as a test file, it must not be deleted unless it is classified as a test file; the non-test functionality required for checklists must remain available.
- Test files in any supported test directory, or using any repository-supported test naming convention, must be included in the deletion scope.
- No implementation change may write to declared security-zone paths; any affected sensitive path requires human handling outside this specification.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide every model required for the checklists experience to load and operate without the DFT-23 crash.
- **FR-002**: System MUST preserve the existing checklist behavior, data meaning, and user-visible outcomes except for eliminating the crash caused by missing models.
- **FR-003**: System MUST handle a checklist with no associated records by presenting the existing or appropriate empty state instead of crashing.
- **FR-004**: System MUST handle missing or unavailable optional checklist relationships without producing the DFT-23 missing-model crash.
- **FR-005**: Repository MUST contain no test files after the DFT-23 change, including files in recognized test directories and files using recognized test naming conventions.
- **FR-006**: The change MUST NOT modify unrelated source files, configuration, documentation, data, or behavior.
- **FR-007**: The implementation MUST NOT add writes within any declared `auth`, `payments`, or `pii` security zone; affected zoned paths are human-gated.
- **FR-008**: The specification's implementation scope MUST be limited to restoring the missing checklist models, deleting all test files, and the minimum supporting changes required for those two outcomes.

### Key Entities *(include if feature involves data)*

- **Checklist**: A user-visible collection or workflow of checklist items; its existing attributes and relationships must remain compatible with current checklist behavior.
- **Checklist Item**: An item belonging to a checklist and represented through the restored model relationships required by the checklist experience.
- **Restored Checklist Model**: Any currently missing domain model required by checklist loading or operations; the exact model names, attributes, and relationships are a MISSING INPUT and must be derived from the repository during planning.
- **Test File**: Any repository file identified by the existing test-directory or test-naming conventions and therefore included in the explicit deletion scope.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of supported checklist entry points load without the DFT-23 crash after the missing models are restored.
- **SC-002**: 100% of checklist model references required by the existing checklist flows resolve successfully, including the empty-checklist case.
- **SC-003**: 100% of repository files classified as test files are absent after the change.
- **SC-004**: The final change set contains no unrelated file or behavior changes beyond the checklist-model restoration and test-file deletion required by DFT-23.

## Assumptions

- The repository's existing checklist flows and conventions define the required model attributes, relationships, and normal empty state; no new checklist behavior is intended.
- The exact missing model names, their current intended definitions, and the checklist crash trace were not provided. **MISSING INPUT**: implementation planning must identify these from the repository and preserve the existing contract.
- The repository's authoritative definition of a “test file” was not provided. **MISSING INPUT**: implementation planning must identify all applicable test directories, filename conventions, generated test artifacts, and test-support files before deleting them.
- “Delete all test files” means delete every repository file classified as a test file, while retaining application source that is needed to restore checklist models.
- No new runtime dependencies are required; introducing one would require human approval under the constitution.
- The requested work is limited to the repository and does not include changes to external services, deployment environments, or declared security-zone paths.
- The specification file itself is not a test file and must remain; the only requested repository output for this task is `./specs/DFT-23/spec.md`.
