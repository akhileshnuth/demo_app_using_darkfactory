# Implementation Plan: Give the App an Actual Visual Design Pass

**Branch**: `DFT-12` | **Date**: 2026-10-12 | **Spec**: [./specs/DFT-12/spec.md](./spec.md)

**Input**: Feature specification from `./specs/DFT-12/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

Create a dependency-free, accessible visual system for the existing Django-rendered application. Centralize tokens and component/state rules in `./static/css/base.css`, establish a responsive shared shell in `./templates/base.html`, and normalize the existing screen templates without changing their workflows, data, or routes. The implementation must include repeatable rendering/responsive/focus verification and a human visual-approval checkpoint. Unreachable Vault CRUD templates are documented as out of scope rather than made functional by this visual-only ticket.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.x, Django 5.2; HTML/CSS templates

**Primary Dependencies**: Existing Django 5.2 and system-font CSS; no new runtime dependency

**Storage**: SQLite in development; unchanged and not touched by this feature

**Testing**: Django `manage.py check` and `manage.py test`; repeatable browser/UI verification with the repository's approved Playwright evidence pattern if the implementation adds that tier

**Target Platform**: Server-rendered web app in current evergreen browsers; verify 320, 375, 768, 1024, and 1280 CSS-pixel viewports

**Project Type**: Django web application

**Performance Goals**: Preserve existing page-load and workflow behavior; no new client runtime or animation budget

**Constraints**: No new runtime dependency, no workflow/data changes, WCAG 2.2 AA contrast target, keyboard-visible focus, forced-colors and reduced-motion-safe CSS, protected-main PR and human visual approval

**Scale/Scope**: Shared shell plus all reachable user-facing templates across auth, dashboard/account, checklists, emergency/notifications, and Vault; one stylesheet and no model/API changes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **PASS** — Spec-Kit workflow is being completed through plan and design artifacts; implementation must continue through tasks, analysis, implementation, convergence, and done.
- **PASS WITH HUMAN GATE** — No security-zone paths or data behavior are planned; verify against `SECURITY_ZONES.md` and factory zone map before implementation if scope expands.
- **PASS** — Delivery remains a pull request against protected `main`, with human review and CI required before merge.
- **PASS** — Existing functional workflows remain covered by tests; any template/interface changes must add repeatable verification for affected states and flows, with CI authoritative.
- **PASS** — No novel runtime dependencies; CSS, semantic HTML, and existing Django capabilities only. Any exception requires human approval.
- **Open human decision** — Approve the derived visual direction (palette, typography, representative screens) before broad implementation; the ticket supplies no brand guide or mockups.

### Post-design re-evaluation

- **PASS** — `research.md`, `data-model.md`, `contracts/ui-visual-treatment.md`, and `quickstart.md` resolve the technical unknowns without adding a data model or runtime dependency.
- **PASS WITH HUMAN GATE** — Human visual approval remains required because exact brand values were not supplied; this is an explicit release checkpoint, not an unresolved implementation dependency.
- **PASS** — The design preserves protected-main PR review, CI authority, test-first verification, and the existing security-zone boundary.

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
config/                     # Django settings and URL configuration (unchanged)
accounts/ dashboard/        # Existing views, forms, and app logic (unchanged)
checklists/ vault/           # Existing workflows and routes (unchanged)
templates/
├── base.html                # Shared responsive shell and navigation
├── registration/            # Login and signup presentation
├── dashboard/               # Dashboard, profile, and activity presentation
├── checklists/              # Checklist, sharing, emergency, and notification screens
└── vault/                   # Reachable Vault screens plus documented orphan templates
static/css/base.css          # Shared tokens, components, states, and responsive rules
```

**Structure Decision**: Keep the existing single Django web application structure. Visual behavior belongs in the shared stylesheet and server-rendered templates; views, models, migrations, URLs, and runtime dependencies remain unchanged unless verification exposes a strictly necessary presentation hook.

## Complexity Tracking

No constitution violations or additional architectural components are planned.
