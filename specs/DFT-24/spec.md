# Feature Specification: Yarn CSS Build and Check Scripts

**Feature Branch**: `DFT-24-yarn-css-scripts`

**Created**: 2026-10-28

**Status**: Draft

**Input**: User description: "Ticket DFT-24: Add yarn scripts to build and check the project's CSS, and run them with yarn"

## Clarifications

### Session 2026-10-28

- Q: Which package manifest should receive the CSS scripts: the existing Node overlay manifest, a new repository-root manifest, or both? → A: Create frontend/package.json with the scripts. Do not use the repository root or overlays/node. If frontend/package.json already exists, add the scripts to it instead of replacing it.
- Q: Because this repository has no CSS build/check toolchain or configuration, should DFT-24 add an approved dev-only CSS toolchain, or should the scripts target tooling supplied by the consuming project? → A: Do not add any third-party packages. The scripts use only Node's built-in modules, in frontend/scripts/build-css.js.
- Q: What exact Yarn script names should expose the two operations? → A: build:css, lint:css and verify. build:css joins every file in frontend/css/ into frontend/dist/app.css using frontend/scripts/build-css.js. lint:css fails if any CSS file has unbalanced curly braces. verify runs lint:css and then build:css.
- Q: Which CSS source and generated output paths should the build command use, given that ./static/css/base.css is the only CSS file and templates currently load it directly? → A: Input: every .css file in frontend/css/, starting with frontend/css/base.css. Output: frontend/dist/app.css. Leave ./static/css/base.css unchanged.
- Q: How should Yarn be integrated with the existing npm-based workflow and CI? → A: Add Yarn-invocable package scripts only; do not change CI or the existing npm workflow.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Build the project's CSS with Yarn (Priority: P1)

As a project contributor, I want a named Yarn script that builds the project's CSS so that I can produce the expected CSS output through the repository's standard package-script interface.

**Why this priority**: Building CSS is the primary capability requested and is needed to generate usable CSS artifacts.

**Independent Test**: From a checkout with the existing CSS toolchain available, invoke the documented Yarn build script and verify that it completes successfully and produces the expected CSS output without requiring a direct tool invocation.

**Acceptance Scenarios**:

1. **Given** the project dependencies and CSS sources are available, **When** a contributor invokes the CSS build script through Yarn, **Then** the project's CSS is built successfully using the existing CSS toolchain.
2. **Given** the CSS build script is invoked through Yarn, **When** the build completes, **Then** the resulting CSS output is available at the project's established output location and the command returns success.

---

### User Story 2 - Check the project's CSS with Yarn (Priority: P1)

As a project contributor or CI job, I want a named Yarn script that checks the project's CSS so that CSS correctness can be verified consistently through Yarn.

**Why this priority**: A check command prevents invalid CSS from being accepted and makes the requested workflow usable in automated validation.

**Independent Test**: Invoke the documented Yarn CSS check script once with valid CSS and once with an intentionally invalid CSS condition, confirming that the first succeeds and the second reports failure.

**Acceptance Scenarios**:

1. **Given** the project's CSS is valid, **When** a contributor invokes the CSS check script through Yarn, **Then** the check completes successfully and returns a success status.
2. **Given** the project's CSS contains a condition rejected by the existing checker, **When** the CSS check script is invoked through Yarn, **Then** it reports the check failure and returns a non-success status.

---

### User Story 3 - Use the CSS scripts consistently in development and CI (Priority: P2)

As a project maintainer, I want the CSS build and check operations exposed as Yarn scripts so that local development and CI use the same named entry points.

**Why this priority**: Consistent invocation reduces command drift and makes the new CSS workflow discoverable and repeatable, after the individual operations are available.

**Independent Test**: Inspect the package-script interface and execute each named CSS operation through Yarn in a clean checkout, confirming that both operations are available without direct invocation of an underlying CSS tool.

**Acceptance Scenarios**:

1. **Given** a clean project checkout, **When** a user lists or invokes the package scripts, **Then** distinct Yarn entry points for CSS building and CSS checking are available.
2. **Given** the CSS scripts are invoked in the supported project environment, **When** either operation finishes, **Then** its exit status and command output accurately communicate success or failure to a caller such as CI.

---

### Edge Cases

- What happens when CSS source files are missing or contain no changes? The build and check scripts should complete according to the existing CSS toolchain's behavior, without silently claiming success when the toolchain reports an error.
- How does the system handle invalid CSS? The check script should surface the checker failure and return a non-success status so automated callers can stop the workflow.
- What happens when required dependencies have not been installed? Yarn should report the missing command or dependency failure clearly and return a non-success status.
- What happens when the CSS output location is not writable? The build script should propagate the write failure rather than masking it.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The project MUST expose a Yarn script that builds the project's CSS through the existing CSS build toolchain.
- **FR-002**: The project MUST expose a Yarn script that checks the project's CSS through the existing CSS checking or validation toolchain.
- **FR-003**: Contributors MUST be able to invoke both CSS operations through Yarn package scripts without directly invoking the underlying CSS tools.
- **FR-004**: The CSS build script MUST return a success status only when the CSS build completes successfully, and MUST propagate build or output errors as a non-success status.
- **FR-005**: The CSS check script MUST return a success status when CSS passes the check and a non-success status when CSS fails the check.
- **FR-006**: The scripts MUST use the project's existing CSS sources, configuration, dependencies, and established output location; this feature MUST NOT introduce a new runtime dependency without human approval.
- **FR-007**: The CSS build and check scripts MUST provide clear command output sufficient for a contributor or CI caller to identify whether the requested operation succeeded or failed.
- **FR-008**: The feature MUST preserve the repository's existing non-CSS Yarn workflows.

### Key Entities *(include if feature involves data)*

- **CSS source set**: The project's existing CSS inputs that are consumed by the build and check operations.
- **CSS build output**: The generated CSS artifact or artifacts written to the project's established output location.
- **Yarn CSS scripts**: The named package-script entry points that expose CSS building and checking to contributors and CI.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a supported checkout with dependencies installed, 100% of invocations of the CSS build script with valid project inputs complete with a success status and produce the established CSS output.
- **SC-002**: In a supported checkout with dependencies installed, 100% of invocations of the CSS check script with valid CSS complete with a success status.
- **SC-003**: In a supported checkout, 100% of CSS check invocations with a deliberately invalid CSS condition return a non-success status and report the failure to the caller.
- **SC-004**: Contributors and CI can invoke both CSS operations using Yarn package scripts only, with no direct underlying-tool command required.

## Assumptions

- The repository already has a CSS build toolchain, CSS checking or validation capability, CSS source files, and an established CSS output location; the ticket does not identify their exact names or paths. **MISSING INPUT**: the existing toolchain commands, configuration, source paths, output paths, and preferred Yarn script names must be confirmed during clarification or planning.
- “Run them with yarn” means both operations must be callable as package scripts through the repository's supported Yarn version and normal dependency-install workflow.
- The feature is limited to adding the two Yarn entry points and wiring them to existing CSS operations; changing CSS behavior, visual design, generated artifact format, or dependency versions is out of scope unless required by the existing toolchain.
- No new runtime dependency is planned; any dependency addition or upgrade that becomes necessary requires human approval under the project constitution.
- CSS build and check commands are expected to be usable in local development and CI, and their process exit statuses are the integration contract for automation.
- This specification plans changes only to non-sensitive project configuration or package-script metadata; it does not plan writes to authentication, payments, PII, or secrets-handling paths.
- The constitution requires the complete Specify → Clarify → Plan → Tasks → Analyze → Implement → Converge → Done pipeline, human review, protected-main pull-request merging, and tests for functional changes; this specification does not authorize implementation or local test execution.
