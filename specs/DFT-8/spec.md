# Feature Specification: Document Vault Core — Categories, Subjects, Types & Documents

**Feature Branch**: `DFT-8-document-vault-core`

**Created**: 2026-09-09

**Status**: Draft

**Input**: User description: "Document vault core: categories, subjects, types & documents"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create and Manage Categories (Priority: P1)

An authenticated user navigates to the vault section of the dashboard, creates a new category (e.g., "Financial", "Legal", "Personal") with a name and optional description, sees it listed in the vault navigation, and can edit or delete it. This is the foundational organizational layer of the document vault — all other vault entities depend on categories existing.

**Why this priority**: Categories are the top-level organizing principle of the vault. Without categories, there is no structure to place documents into. This is the minimum viable vault: a user can create one or more categories and begin organizing. It establishes the vault navigation pattern and CRUD conventions that all subsequent vault features build upon.

**Independent Test**: Can be fully tested by navigating to the vault, creating a category, verifying it appears in the vault list, editing its name, and deleting it. Delivers a working organizational skeleton for the document vault.

**Acceptance Scenarios**:

1. **Given** an authenticated user on the vault page, **When** they submit a new category with a valid name, **Then** the category is created and appears in the vault category list.
2. **Given** an authenticated user on the vault page with an existing category, **When** they edit the category's name or description and save, **Then** the updated values are persisted and reflected in the list.
3. **Given** an authenticated user on the vault page with an existing category, **When** they delete the category, **Then** the category is removed from the list. [NEEDS CLARIFICATION: what happens to documents assigned to a deleted category — are they orphaned, reassigned, or is deletion blocked?]
4. **Given** an authenticated user on the vault page, **When** they attempt to create a category with a name that already exists, **Then** the system rejects the submission with a validation error indicating the name is a duplicate.
5. **Given** an authenticated user on the vault page, **When** they attempt to create a category with an empty name, **Then** the system rejects the submission with a validation error.

---

### User Story 2 - Create and Manage Subjects (Priority: P2)

An authenticated user creates subjects (e.g., "Tax Returns", "Client Agreements") that represent topics within the vault. Subjects are independent of categories and can be associated with documents later. The user can list, create, edit, and delete subjects from the vault management interface.

**Why this priority**: Subjects are the second organizational layer and are required before documents can be meaningfully classified. They sit alongside categories as the two axes by which documents are organized. This priority reflects that subjects depend on the vault navigation and CRUD patterns established in User Story 1.

**Independent Test**: Can be fully tested by navigating to the subjects management view, creating a subject, verifying it appears in the list, editing it, and deleting it. Delivers a functional subject taxonomy for the vault.

**Acceptance Scenarios**:

1. **Given** an authenticated user on the subjects management page, **When** they submit a new subject with a valid name, **Then** the subject is created and appears in the subjects list.
2. **Given** an authenticated user on the subjects management page, **When** they edit a subject's name or description and save, **Then** the updated values are persisted.
3. **Given** an authenticated user on the subjects management page, **When** they attempt to create a subject with a duplicate name, **Then** the system rejects the submission with a validation error.
4. **Given** an authenticated user on the subjects management page with an existing subject, **When** they delete the subject, **Then** the subject is removed from the list.

---

### User Story 3 - Create and Manage Document Types (Priority: P2)

An authenticated user creates document types (e.g., "Invoice", "Contract", "Receipt", "Correspondence") that classify the nature or format of documents. The user can list, create, edit, and delete document types from the vault management interface.

**Why this priority**: Document types are a classification taxonomy that is independent of categories and subjects. They are co-equal with subjects in priority because both are required to fully classify a document before documents can be created (User Story 4). This story can be developed in parallel with User Story 2.

**Independent Test**: Can be fully tested by navigating to the document types management view, creating a type, verifying it appears in the list, editing it, and deleting it. Delivers a functional type taxonomy for the vault.

**Acceptance Scenarios**:

1. **Given** an authenticated user on the document types management page, **When** they submit a new type with a valid name, **Then** the type is created and appears in the types list.
2. **Given** an authenticated user on the document types management page, **When** they edit a type's name or description and save, **Then** the updated values are persisted.
3. **Given** an authenticated user on the document types management page, **When** they attempt to create a type with a duplicate name, **Then** the system rejects the submission with a validation error.
4. **Given** an authenticated user on the document types management page with an existing type, **When** they delete the type, **Then** the type is removed from the list.

---

### User Story 4 - Create and View Documents in the Vault (Priority: P2)

An authenticated user creates a document record in the vault by providing a title, selecting a category, subject, and document type, and optionally adding notes. They can then view the document in the vault list and see its details. This is the core entity that ties all taxonomy together.

**Why this priority**: The document record is the central entity of the vault. It depends on categories, subjects, and types being in place. This story delivers the actual value proposition of the vault — storing and organizing document records. It is P2 because the taxonomy infrastructure (User Stories 1-3) must exist first, but it is the primary deliverable of this ticket.

**Independent Test**: Can be fully tested by creating categories, subjects, and types, then creating a document record linked to them, verifying it appears in the vault list, and viewing its detail page. Delivers a functional document vault.

**Acceptance Scenarios**:

1. **Given** an authenticated user with existing categories, subjects, and types, **When** they create a document with a title, category, subject, type, and optional notes, **Then** the document is created and appears in the vault document list.
2. **Given** an authenticated user on the vault document list, **When** they click on a document, **Then** they see the document detail page showing title, category, subject, type, notes, and timestamps (created, updated).
3. **Given** an authenticated user creating a document, **When** they leave the title blank or fail to select a category, subject, or type, **Then** the system rejects the submission with validation errors indicating the missing required fields.
4. **Given** an authenticated user on the vault document list, **When** they view the list, **Then** documents are sorted by most recently updated first.
5. **Given** an authenticated user on the vault document list, **When** they attempt to create a document with a duplicate title, **Then** the system rejects the submission with a validation error indicating the title is a duplicate.

---

### User Story 5 - Edit and Delete Documents (Priority: P3)

An authenticated user can edit an existing document's title, category, subject, type, and notes. They can also delete a document from the vault. This completes the document lifecycle management.

**Why this priority**: Edit and delete are natural extensions of the document CRUD cycle. They are lower priority because the core vault value (creating and viewing documents) is delivered in User Story 4. These operations round out the management capabilities.

**Independent Test**: Can be fully tested by creating a document, editing its fields, verifying changes persist, and then deleting the document and verifying it no longer appears in the list.

**Acceptance Scenarios**:

1. **Given** an authenticated user on the document detail page, **When** they edit the document's title, category, subject, type, or notes and save, **Then** the updated values are persisted and reflected on the detail page.
2. **Given** an authenticated user on the vault document list, **When** they delete a document, **Then** the document is removed from the list and no longer accessible.
3. **Given** an authenticated user editing a document, **When** they attempt to save without a title or without a selected category/subject/type, **Then** the system rejects the submission with validation errors.

---

### User Story 6 - Browse and Filter Vault Documents (Priority: P3)

An authenticated user can filter the vault document list by category, subject, or type. They can also search documents by title. This makes the vault usable once it contains more than a handful of documents.

**Why this priority**: Filtering and search become valuable only after documents accumulate. They are essential for a usable vault but are not required for the initial data model and CRUD foundation.

**Independent Test**: Can be fully tested by creating multiple documents with different categories/subjects/types, applying filters, and verifying only matching documents appear.

**Acceptance Scenarios**:

1. **Given** an authenticated user on the vault document list, **When** they select a category filter, **Then** only documents in that category are displayed.
2. **Given** an authenticated user on the vault document list, **When** they enter a search term in the title search, **Then** only documents whose title contains the search term are displayed.
3. **Given** an authenticated user on the vault document list, **When** they clear all filters, **Then** all documents are displayed again.

---

### Edge Cases

- What happens when a user attempts to delete a category that has documents assigned to it? Is the deletion blocked, or are the documents orphaned (category set to null)?
- What happens when a user attempts to delete a subject or type that is assigned to existing documents?
- How does the system handle a user who creates a very large number of categories, subjects, or types — is there a practical limit?
- What happens when a document's category, subject, or type is edited while another user is viewing the same document?
- How does the system handle concurrent creation of documents with the same title by the same user?
- What happens when a user attempts to upload a file attachment to a document? [NEEDS CLARIFICATION: the ticket says "documents" but does not specify whether actual file upload is in scope or only document metadata records]

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a `vault` Django app containing the data models and views for categories, subjects, document types, and documents.
- **FR-002**: System MUST persist categories with at minimum: name (unique, required), description (optional), and timestamps (created, updated).
- **FR-003**: System MUST persist subjects with at minimum: name (unique, required), description (optional), and timestamps (created, updated).
- **FR-004**: System MUST persist document types with at minimum: name (unique, required), description (optional), and timestamps (created, updated).
- **FR-005**: System MUST persist documents with at minimum: title (required), notes (optional), and timestamps (created, updated). Each document MUST be linked to exactly one category, one subject, and one document type via foreign key relationships.
- **FR-006**: System MUST link each document to the authenticated user who created it (owner relationship).
- **FR-007**: System MUST provide list, create, edit, and delete views for categories accessible at vault-related URL paths.
- **FR-008**: System MUST provide list, create, edit, and delete views for subjects accessible at vault-related URL paths.
- **FR-009**: System MUST provide list, create, edit, and delete views for document types accessible at vault-related URL paths.
- **FR-010**: System MUST provide list, create, detail, edit, and delete views for documents accessible at vault-related URL paths.
- **FR-011**: System MUST enforce authentication on all vault views, redirecting unauthenticated requests to the login page.
- **FR-012**: System MUST enforce that each authenticated user can only see and manage their own documents. Categories, subjects, and types are shared across all users.
- **FR-013**: System MUST validate that document titles are unique per user (a user cannot have two documents with the same title, but different users may).
- **FR-014**: System MUST validate that category, subject, and type names are unique globally.
- **FR-015**: System MUST enforce CSRF protection on all state-changing vault operations.
- **FR-016**: System MUST register the `vault` app in `INSTALLED_APPS` in `config/settings.py`.
- **FR-017**: System MUST include vault URL patterns in the root URL configuration (`config/urls.py`).
- **FR-018**: System MUST integrate vault navigation links into the dashboard sidebar template so authenticated users can access the vault from the dashboard shell.
- **FR-019**: System MUST render all vault forms with server-side validation errors displayed inline next to the relevant field.
- **FR-020**: System MUST provide Django admin registrations for Category, Subject, DocumentType, and Document models for administrative management.

### Key Entities

- **Category**: The top-level organizational unit in the vault. Represents a broad grouping of documents (e.g., "Financial", "Legal", "Personal"). Key attributes: name (unique, required), description (optional), created timestamp, updated timestamp. A category can have many documents. Categories are shared across all users.
- **Subject**: A topic or sub-area within the vault. Represents a specific subject matter documents relate to (e.g., "Tax Returns", "Client Agreements"). Key attributes: name (unique, required), description (optional), created timestamp, updated timestamp. A subject can have many documents. Subjects are shared across all users.
- **DocumentType**: A classification label for documents (e.g., "Invoice", "Contract", "Receipt"). Key attributes: name (unique, required), description (optional), created timestamp, updated timestamp. A type can be applied to many documents. Types are shared across all users.
- **Document**: The central entity of the vault. Represents a single document record with metadata. Key attributes: title (required, unique per user), notes (optional), created timestamp, updated timestamp. Relationships: belongs to exactly one Category, exactly one Subject, exactly one DocumentType, and is owned by exactly one User. Documents are scoped to their owner — a user sees only their own documents.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An authenticated user can create a category, subject, and document type, then create a document linked to all three, and view it in the vault list — all within 3 minutes from first vault navigation.
- **SC-002**: The vault document list correctly displays only the authenticated user's documents, with no cross-user data leakage, verified by creating two users and confirming isolated vault contents.
- **SC-003**: 100% of unauthenticated requests to any vault URL result in a redirect to the login page with zero data leakage.
- **SC-004**: All vault CRUD operations (create, edit, delete) for categories, subjects, types, and documents complete without errors and persist changes correctly in the database.
- **SC-005**: The Django test suite passes with zero failures on CI for all vault-related tests (models, views, forms, URLs).
- **SC-006**: Duplicate name validation prevents creation of categories, subjects, or types with existing names, and prevents creation of documents with duplicate titles per user.
- **SC-007**: Vault navigation links appear in the dashboard sidebar and correctly route to the vault views.

## Assumptions

- The document vault is a new Django app (`vault`) added to the existing project scaffolded in DFT-7. It does not modify the `accounts` or `dashboard` apps except for adding vault navigation links to the dashboard sidebar.
- "Documents" in this ticket refers to document metadata records (title, notes, category/subject/type associations), not actual file uploads. File attachment handling is out of scope unless explicitly added to the ticket. [NEEDS CLARIFICATION: the ticket says "documents" but does not specify file upload — this spec assumes metadata-only records. If file upload is intended, the spec must be updated.]
- Categories, subjects, and document types are shared resources visible and manageable by all authenticated users. Only documents are scoped to individual users.
- Database for development and testing remains SQLite (Django default), consistent with DFT-7.
- The vault will use Django's built-in class-based views (generic CRUD views) consistent with the pattern established in the dashboard app.
- Server-rendered Django templates (no frontend JavaScript framework) are used for all vault views, consistent with DFT-7.
- The vault does not touch any declared security zones (`src/auth`, `src/payments`, `src/customers`). No writes occur in protected paths.
- No novel runtime dependencies are required beyond Django itself; this ticket is autonomy-eligible under Constitution Principle V.
- The dashboard sidebar will need a minor template update to include vault navigation links — this is a minimal change to the existing `dashboard` app template, not a structural modification.
- Delete behavior for categories/subjects/types that have assigned documents is not specified in the ticket. This spec assumes deletion is blocked with an error message when documents exist, but this requires confirmation. [NEEDS CLARIFICATION: should deletion be blocked, cascading, or set-null when associated documents exist?]
