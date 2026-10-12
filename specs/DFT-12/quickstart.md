# DFT-12 Validation Guide

## Prerequisites

- Python environment with `Django~=5.2` installed from `./requirements.txt`.
- From the repository root (`/work`), use the existing SQLite development database or a test database.
- For UI evidence, use the system Chromium and the repository's documented Playwright constraints in `./overlays/node/PLAYWRIGHT.md`; do not download a browser in the sandbox.

## Baseline and regression checks

```bash
python manage.py check
python manage.py test
```

Expected result: Django reports no configuration errors and all existing workflow tests pass.

## Repeatable visual-flow matrix

For authenticated and anonymous entry points, exercise the reachable screens in the inventory: login/signup, dashboard, profile/activity, checklist list/form/detail/share, shared checklist, emergency contacts/request/respond, notifications, and reachable Vault list/export flows.

At each viewport (320, 375, 768, 1024, 1280 CSS px), verify:

1. The page title/purpose and intended primary action are obvious.
2. Navigation, links, buttons, forms, inline actions, and pagination remain reachable with keyboard only.
3. Every focused element has a visible non-color-only indicator.
4. Empty, validation-error, message, disabled, selected/unread, destructive-confirmation, and read-only states remain intentional and legible.
5. Long titles/emails/messages wrap without clipping or horizontal loss; Vault tables preserve essential content through their responsive strategy.
6. `prefers-reduced-motion` and forced-colors/high-contrast behavior do not remove meaning or focus.

Use the UI contract in `./specs/DFT-12/contracts/ui-visual-treatment.md` as the assertion checklist. Human reviewers additionally approve representative auth, dashboard, checklist detail/form, notification, and Vault screens for typography, spacing, color roles, surfaces, and hierarchy.

## CI/release evidence

The pull request MUST show green Django checks and the repeatable UI verification for affected screens. CI is authoritative; merge remains blocked until human review approves the visual direction and the pull request targets protected `main`.
