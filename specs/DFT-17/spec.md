# Feature Specification: Protect Uploaded Documents

**Feature Branch**: `017-protect-uploaded-documents`

**Created**: 2026-10-12

**Status**: Draft

**Input**: User description: "Ticket DFT-17: Uploaded documents aren't actually protected"

## Clarifications

### Session 2026-10-12

- Q: The ticket says uploaded documents are not protected, but the repository's Document model and form currently store only metadata and the vault has no document retrieval endpoint: should this feature implement file upload, private storage, and authorized retrieval end to end, or only protect an upload/retrieval capability supplied separately? → A: Implement the file upload, private storage, and authorized retrieval flow in this feature; the current repository has no document content or retrieval path to secure.
- Q: Which users should a document's access policy allow? → A: The owner and explicitly listed per-document collaborators
- Q: Where must uploaded document bytes be stored, and how must an authorized retrieval deliver them, given that the repository has no configured media storage or protected file endpoint? → A: Store bytes in a private, non-public storage location and deliver them only through an application endpoint that checks the current policy before streaming; do not expose a static or identifier-only URL.
- Q: Which audit destination should record successful and denied document access decisions, including unauthenticated or otherwise unresolvable requesters? → A: Extend the existing accounts.ActivityLog with document-access event types and nullable or anonymous actor context
- Q: What response policy should apply to document requests that lack permission? → A: Redirect unauthenticated users to login and return a non-disclosing 404 for authenticated users without access
- Q: What is the required treatment of documents that already exist when this protection is released, including incident response if their bytes were previously public or unprotected? → A: Inventory all pre-existing documents, move or re-protect their bytes before enabling retrieval, and explicitly record any exposure-handling decision; do not leave legacy documents retrievable during rollout.
- Q: Should an expired document be denied by the retrieval endpoint, and what should happen to its stored bytes after expiry or deletion? → A: Deny retrieval as soon as expiry takes effect, remove or quarantine stored bytes on deletion, and return the same non-disclosing failure for expired or deleted identifiers as for inaccessible documents.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Enforce document access controls (Priority: P1)

As a document owner or an authorized collaborator, I want uploaded documents to be accessible only to permitted users so that private content is not exposed to unauthorized parties.

**Why this priority**: Preventing unauthorized disclosure is the primary problem identified by the ticket and is required before the upload feature can be considered protected.

**Independent Test**: Upload a document as one user, attempt to access it as an unauthorized user and as an authorized user, and verify that only the authorized user receives the document.

**Acceptance Scenarios**:

1. **Given** a document owned by User A, **When** User B has no permission for that document and requests it, **Then** the document content is not disclosed and the request is rejected with the system's standard unauthorized or forbidden response.
2. **Given** a document owned by User A, **When** User A or an explicitly authorized collaborator requests it, **Then** the document is returned through the normal document access flow.

---

### User Story 2 - Protect documents throughout their lifecycle (Priority: P2)

As a user who uploads a document, I want its stored representation and access path to remain protected after upload so that protection is not lost between submission, storage, and retrieval.

**Why this priority**: The ticket indicates that uploaded documents are not actually protected; protection must cover persisted documents and not only the upload interaction.

**Independent Test**: Upload a document, verify that direct access without authorization does not reveal its contents, then retrieve it through an authorized flow and verify the content is intact.

**Acceptance Scenarios**:

1. **Given** a successfully uploaded document, **When** a requester bypasses the normal authorized retrieval flow, **Then** the document contents and an unrestricted public location are not exposed.
2. **Given** a successfully uploaded document, **When** an authorized requester retrieves it, **Then** the requester receives the original document without weakening the document's access restrictions.

---

### User Story 3 - Record protection-relevant access events (Priority: P3)

As a system operator, I want document access decisions and failed access attempts to be attributable so that suspected exposure can be investigated without recording document contents.

**Why this priority**: Auditable outcomes support detection and investigation, but access enforcement is the immediate protection requirement.

**Independent Test**: Perform an authorized retrieval and an unauthorized retrieval, then inspect the available security audit record to confirm both decisions are attributable and that document content is absent.

**Acceptance Scenarios**:

1. **Given** an attempted document access, **When** the system allows or rejects the request, **Then** it records the decision with the document reference, requester or actor context, timestamp, and outcome without recording document contents.

---

### Edge Cases

- When a document has no owner or its permissions cannot be resolved, the system must fail closed and must not disclose the document.
- When a user's permission is removed while a document is being accessed, the system must not grant access based solely on stale permission information.
- When a document identifier is guessed, altered, or reused, the response must not reveal whether another user's document exists.
- When an upload, protection step, or storage operation fails partway through, the system must not leave an accessible unprotected copy.
- When a document is deleted or expires, subsequent retrieval attempts must not return its contents.
- When audit recording fails, the system must follow the repository's security policy and must not silently turn a denied access into an allowed access.
- When an authorized document is unavailable or corrupted, the system must report the failure without exposing another document or sensitive storage details.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST associate every uploaded document with an owner and an explicit access policy before the document can be retrieved.
- **FR-002**: System MUST enforce the document's access policy on every document retrieval request, including requests made through direct or alternate access paths.
- **FR-003**: System MUST deny document access when the requester is unauthenticated, unauthorized, or cannot be reliably associated with an allowed identity.
- **FR-004**: System MUST fail closed when document ownership, permissions, document state, or protection status cannot be determined.
- **FR-005**: System MUST prevent uploaded document contents from being publicly reachable or retrievable through an identifier alone.
- **FR-006**: System MUST ensure that a document is not available for retrieval until its required protection and access-control state has been established.
- **FR-007**: System MUST preserve the existing authorized upload and retrieval experience for document owners and explicitly authorized collaborators, subject to the enforced access policy.
- **FR-008**: System MUST return a safe, consistent failure response for denied access without disclosing document existence, contents, ownership, or storage details to unauthorized requesters.
- **FR-009**: System MUST record successful and denied document access decisions with sufficient actor, document-reference, timestamp, and outcome information for security investigation.
- **FR-010**: System MUST NOT record uploaded document contents or sensitive document data in security audit records.
- **FR-011**: System MUST ensure that partial failures, deletion, and expiration cannot leave a retrievable document outside the applicable access policy.
- **FR-012**: System MUST keep all document-protection data and operations within the repository's approved security boundaries; no specification work authorizes writes to declared sensitive security-zone paths.

### Key Entities *(include if feature involves data)*

- **Uploaded Document**: A user-provided file and its lifecycle state, including ownership, content reference, and whether it is available for authorized retrieval.
- **Document Access Policy**: The permissions associated with an uploaded document, identifying the owner and any explicitly authorized collaborators or access conditions.
- **Access Decision**: The allow or deny result for a document request, including the actor context, document reference, timestamp, and reason or outcome.
- **Security Audit Record**: A non-content record of document access attempts and protection-relevant state changes used for investigation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In security acceptance testing, 100% of retrieval attempts by users without document permission are denied without document-content disclosure.
- **SC-002**: In security acceptance testing, 100% of retrieval attempts by the document owner or an explicitly authorized collaborator succeed when the document is available and intact.
- **SC-003**: 100% of uploaded documents are unavailable for retrieval until their owner, access policy, and protected state are established.
- **SC-004**: 100% of successful and denied document access attempts produce an attributable audit record that contains no document contents.
- **SC-005**: No tested direct, guessed, altered, or alternate document access path bypasses the applicable access policy.

## Assumptions

- The affected workflow includes an existing upload and retrieval capability, and this feature strengthens its protection rather than introducing a separate document product.
- Users and collaborators can already be identified by the repository's existing authentication and authorization context; the ticket does not specify a new identity mechanism.
- The existing document ownership and sharing model is the intended source of permission truth; exact permission roles and inheritance rules are a MISSING INPUT and must be confirmed during clarification.
- The exact current storage, retrieval, and exposure paths are a MISSING INPUT; the implementation plan must inventory them without writing to any declared `auth`, `payments`, or `pii` security-zone path.
- The required protection mechanism for stored documents and in transit is a MISSING INPUT; this specification requires effective protection and access enforcement without prescribing an unapproved technology or dependency.
- The repository's standard response format, audit destination, retention period, and incident-handling policy are MISSING INPUTS; clarification must establish them before implementation.
- Existing documents uploaded before this feature may already be exposed; migration, re-protection, and incident response for pre-existing documents are MISSING INPUTS and must be explicitly scoped during clarification.
- Mobile-specific behavior, public sharing, downloads, previews, and document transformations are not described by the ticket; their treatment is a MISSING INPUT unless they use the same document access paths.
- Functional implementation changes will require tests and a human-reviewed pull request under the project constitution; this specification does not authorize source-code changes or writes in security zones.
