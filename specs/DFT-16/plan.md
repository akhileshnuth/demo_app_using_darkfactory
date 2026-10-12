# Implementation Plan: Add a Copyright Footer to the Base Template

**Branch**: `DFT-16` | **Date**: 2026-10-12 | **Spec**: [./spec.md]

**Input**: Feature specification from [./spec.md]

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

Add one semantic footer to the shared Django base template with the approved static
notice `Copyright 2026 Daylight. All rights reserved.`. Place it outside the
overridable `shell` block so authenticated pages and pages such as login that
replace that block receive the same footer. Existing `base.css` footer and mobile
rules already provide readable presentation, so no CSS change is planned.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python (repository Django application; interpreter version is not pinned in the repo)

**Primary Dependencies**: Django ~= 5.2; no new dependencies

**Storage**: N/A; static template markup only

**Testing**: Django `TestCase` via `python manage.py test`; targeted tests in `./tests/test_visual_design.py`

**Target Platform**: Django-rendered web pages in supported browsers

**Project Type**: Django web application

**Performance Goals**: No measurable runtime impact; one static element per rendered base layout

**Constraints**: Preserve existing shell/content blocks, use semantic HTML, avoid security-zone paths, and add no runtime dependency

**Scale/Scope**: One shared template, all views inheriting `base.html`, and representative authenticated/unauthenticated rendering tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Spec-Kit completeness**: PASS for this planning phase; the implementation must continue through Tasks, Analyze, Implement, and review.
- **Security zones**: PASS; planned paths (`./templates/base.html` and `./tests/test_visual_design.py`) are outside the declared auth, payments, and PII paths.
- **Human-gated merge**: PASS; delivery remains a pull request against protected `main` with human review and CI.
- **Test-first**: PASS with implementation condition; tests must be added/updated alongside the template change and CI remains authoritative.
- **Dependencies**: PASS; no new runtime dependency is needed.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
templates/
└── base.html                 # shared layout; add the semantic footer

static/css/
└── base.css                  # existing footer presentation; no planned change

tests/
└── test_visual_design.py     # rendered footer/content assertions
```

**Structure Decision**: Use the existing Django template/static/test structure.
The footer belongs in `./templates/base.html`, outside `{% block shell %}`;
rendering coverage belongs in `./tests/test_visual_design.py`. No view, URL,
model, migration, or CSS file change is required.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | The feature fits the existing shared-template structure. |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
