# Feature Specification: Document Vault Core: Categories, Subjects, Types & Documents

**Feature Branch**: `DFT-8-document-vault-core`

**Created**: 2026-10-12

**Status**: Draft

**Input**: User description: "Ticket DFT-8: Document vault core: categories, subjects, types & documents"

## Clarifications

### Session 2026-10-12

- Q: Should a Document include an actual file payload or content reference, or remain a metadata-only record for this release? → A: Metadata-only records; defer file upload and content storage to a separate feature
- Q: Who may create, edit, and delete the shared categories, subjects, and document types? → A: Staff or administrator users only
- Q: Should DFT-8 preserve the existing Document expiry and reminder behavior already present in the repository? → A: Preserve the existing expiry fields and reminder integration while adding the DFT-8 lifecycle
- Q: Which document-list URL should be canonical, and how should the existing route be handled? → A: Make /vault/ canonical and redirect the existing /vault/documents/ route to it

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Organize the vault taxonomy (Priority: P1)

As a vault administrator, I want to create and manage categories, subjects, and document types so that documents can be organized consistently.

**Why this priority**: The taxonomy is the foundation for finding and classifying every document in the vault.

**Independent Test**: Can be tested by creating, viewing, updating, and removing taxonomy records and confirming that the resulting records are available for document classification.

**Acceptance Scenarios**:

1. **Given** an empty or existing vault, **When** an administrator creates a category, subject, or document type with a valid name, **Then** the new taxonomy record is persisted and appears in the relevant list.
2. **Given** an existing taxonomy record that is not required by another record, **When** an administrator updates or removes it, **Then** the vault reflects the change and no stale record is shown.

---

### User Story 2 - Create and classify documents (Priority: P2)

As a vault user, I want to add documents and assign their category, subject, and type so that each document has useful, structured classification.

**Why this priority**: A taxonomy has practical value only when users can place documents into it and maintain document records.

**Independent Test**: Can be tested by adding a document with valid metadata, associating it with existing taxonomy records, and verifying the document and associations afterward.

**Acceptance Scenarios**:

1. **Given** existing category, subject, and type records, **When** a user adds a document and selects those records, **Then** the document is persisted with the selected classification and can be retrieved from the vault.
2. **Given** an existing document, **When** a user edits its metadata or classification, **Then** the updated document details are persisted without changing unrelated documents.

---

### User Story 3 - Browse and maintain vault records (Priority: P3)

As a vault user, I want to browse documents and their classification details so that I can identify, review, and maintain the records in the vault.

**Why this priority**: Clear retrieval and safe maintenance make the core records usable after they are created.

**Independent Test**: Can be tested with a vault containing multiple documents and taxonomy records by listing records, opening a document, and attempting valid and invalid maintenance actions.

**Acceptance Scenarios**:

1. **Given** multiple documents with different classifications, **When** a user browses the vault or filters by an available taxonomy value, **Then** matching documents and their classification details are shown.
2. **Given** a document or taxonomy record referenced by another record, **When** a user attempts to remove it, **Then** the system prevents an invalid removal and explains that the reference must be resolved first.

---

### Edge Cases

- A category, subject, or document type name that is blank or duplicates an existing name is rejected with a clear validation message.
- A document is submitted without required classification or with a taxonomy reference that does not exist; the document is not partially persisted and the user is told what must be corrected.
- An attempt is made to remove a taxonomy record referenced by one or more documents; the system preserves referential integrity and reports the dependency.
- A requested document or taxonomy record does not exist; the system returns a not-found result without exposing unrelated records.
- A document update changes only the supplied fields; concurrent or unrelated records remain unchanged.
- A document has an unsupported, empty, or excessively large file payload; the system rejects it with a user-actionable error. Exact supported formats and size limits are [NEEDS CLARIFICATION: not specified by the ticket].

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow authorized users to create, view, update, and remove categories.
- **FR-002**: System MUST allow authorized users to create, view, update, and remove subjects.
- **FR-003**: System MUST allow authorized users to create, view, update, and remove document types.
- **FR-004**: System MUST validate required taxonomy names and prevent duplicate names within the applicable taxonomy collection.
- **FR-005**: System MUST allow authorized users to create, view, update, and remove document records.
- **FR-006**: Documents MUST support association with a category, a subject, and a document type.
- **FR-007**: System MUST persist document metadata and its taxonomy associations so they are available after the original operation completes.
- **FR-008**: System MUST allow users to browse documents and view their associated category, subject, and type.
- **FR-009**: System MUST support narrowing the document list by available category, subject, and document type values.
- **FR-010**: System MUST reject invalid, missing, or stale references and MUST NOT persist partial records when validation fails.
- **FR-011**: System MUST prevent removal of a category, subject, or document type while it is referenced by a document, unless an explicit reassignment or deletion policy is provided.
- **FR-012**: System MUST enforce the existing authorization model for all vault operations; the ticket does not specify the authentication or authorization mechanism.
- **FR-013**: System MUST avoid writes to the constitution's protected `src/auth`, `src/payments`, and `src/customers` security-zone paths.
- **FR-014**: Any functional implementation MUST include automated tests, and any new runtime dependency requires human approval.

### Key Entities *(include if feature involves data)*

- **Category**: A top-level classification used to organize documents; includes a unique name and may be referenced by many documents.
- **Subject**: A classification describing the subject matter of documents; includes a unique name and may be referenced by many documents.
- **Document Type**: A classification describing the kind or format of a document; includes a unique name and may be referenced by many documents.
- **Document**: A vault record representing a stored document and its metadata, including its name or title, content reference, and associations to one category, one subject, and one document type.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of valid create, update, view, and remove operations for categories, subjects, and document types produce the expected persisted state in acceptance testing.
- **SC-002**: 100% of valid test documents can be created with category, subject, and type associations and retrieved with those associations intact.
- **SC-003**: 100% of tested invalid names, missing required fields, stale references, and protected-reference removals are rejected without partial persistence.
- **SC-004**: Users can locate all documents matching a selected category, subject, or document type in one browsing flow, with no unrelated documents included.

## Assumptions

- The target users are authorized vault administrators and users; the existing project authorization model is reused rather than redesigned.
- “Core” means taxonomy and document record lifecycle, classification, browsing, and validation. Sharing, version history, workflow, full-text search, retention, audit reporting, and bulk import/export are out of scope unless separately specified.
- A document has one category, one subject, and one document type in the initial model; many-to-many classification is not assumed.
- Document content is expected to be stored or referenced by the existing project document-storage mechanism; the ticket does not identify that mechanism.
- **MISSING INPUT**: No design file, wiki page, API contract, data model, supported file-format list, size limit, retention policy, or authorization details were provided. The specification therefore leaves those details to clarification and requires compatibility with the existing project conventions.
- Taxonomy names are unique within each taxonomy, case-insensitively unless existing project rules specify otherwise.
- Implementation must follow the constitution's complete Spec-Kit pipeline, human-gated pull-request merge, test-first requirement, and approval requirement for novel runtime dependencies.
