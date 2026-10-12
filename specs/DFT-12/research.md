# Research: DFT-12 Visual Design Pass

## Decision: Use a small, dependency-free CSS design system

**Rationale:** The app is a Django 5.2 server-rendered application with one stylesheet and no active root frontend build. Define semantic custom properties, typography, spacing, surfaces, controls, feedback, and state selectors in `./static/css/base.css`; use semantic HTML and existing Django rendering. This satisfies the no-novel-dependency constraint and avoids a framework migration.

**Alternatives considered:** Bootstrap/Tailwind would add dependency or build/markup migration cost; external fonts add network and layout-shift risk; JavaScript menus are unnecessary for essential navigation.

## Decision: Treat all reachable user-facing templates as the visual inventory

**Rationale:** The primary product surface spans auth, dashboard/account, checklist, emergency/notification, and Vault screens. Shared treatment must be established in `./templates/base.html` and applied consistently to those templates. Existing workflows, routes, data, and content remain unchanged.

**Alternatives considered:** Styling only the checklist templates would leave the shared shell, auth, account, and Vault surfaces inconsistent. Completing missing Vault CRUD routes would expand a visual ticket into functional work, so orphaned route references are explicitly excluded and recorded for a separate decision.

## Decision: Use responsive breakpoints and a viewport matrix

**Rationale:** Existing support is implicit rather than documented. Verify 320px, 375px, 768px, 1024px, and 1280px, with layout changes around 48rem and 64rem. Keep tabular Vault data semantic inside an overflow container, and preserve essential actions on narrow screens.

**Alternatives considered:** Keeping only the existing 600px breakpoint does not address dense forms, tables, inline actions, or long content at intermediate widths; replacing tables with cards risks losing comparison semantics.

## Decision: Make state and accessibility semantics explicit

**Rationale:** Define visible `:focus-visible` rings that are not color-only, hover/active/selected/disabled/error/success/empty/loading treatments, readable contrast targets (WCAG 2.2 AA), forced-colors-safe borders/text, and reduced-motion-safe behavior. Add labels/roles only where needed and retain semantic controls.

**Alternatives considered:** Color-only status indicators and screenshots-only testing do not prove accessibility, keyboard use, or forced-colors behavior.

## Decision: Combine Django regression checks, repeatable UI checks, and human review

**Rationale:** Existing Django tests use `TestCase` and HTML assertions but do not exercise CSS, focus, or viewport behavior. Preserve `python manage.py check` and `python manage.py test`; add a repeatable browser/UI matrix following `./overlays/node/PLAYWRIGHT.md` only if the implementation activates that evidence tier. Human review remains required for hierarchy, spacing, palette, and visual consistency.

**Alternatives considered:** Existing backend tests alone cannot verify focus, overflow, states, or visual hierarchy; screenshots alone cannot verify semantics or workflows.

## Resolved clarification: Visual direction and missing design assets

No brand guide, mocks, or screen inventory were supplied. The implementation baseline is a calm, security-oriented neutral system using system fonts, navy text, cool neutral canvas, white surfaces, blue-teal accent, semantic success/warning/error roles, a 4px spacing base, restrained borders/shadows, and two radii. Human approval of representative screens is a release gate before broad rollout.
