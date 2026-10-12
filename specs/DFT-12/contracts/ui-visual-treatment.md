# UI Contract: Visual Treatment and Responsive Presentation

This is a server-rendered UI contract, not a public data API.

## Shared shell

`./templates/base.html` MUST provide one consistent authenticated navigation/header structure, a keyboard-accessible path to main content, a visible current/selected navigation state where applicable, and header actions that remain reachable on narrow screens. Public auth templates MUST use the same tokens and control treatments even when they do not use the authenticated shell.

## Component roles

- **Primary action:** visually strongest action for the page/workflow.
- **Secondary action:** supportive navigation or reversible action with lower emphasis.
- **Destructive action:** visually distinct and separated from ordinary actions; existing confirmation workflows remain intact.
- **Feedback:** success, warning, error, empty, loading, and unread/selected states use semantic text/structure plus visual distinction, never color alone.
- **Form controls:** labels remain associated; validation errors appear near their field and at any existing form-level error location; disabled controls remain legible and visibly unavailable.
- **Data tables:** retain table semantics, readable headers, and a narrow-screen strategy that does not hide essential content.

## Interaction and accessibility

Every focusable control MUST have a visible `:focus-visible` indicator distinct from surrounding borders and understandable without color alone. Hover MUST not be the sole way to discover an action. The treatment MUST remain usable with keyboard navigation, `prefers-reduced-motion`, and `forced-colors: active`.

## Responsive contract

Validate at 320px, 375px, 768px, 1024px, and 1280px. No essential content/action may be clipped, overlapped, or unreachable; long titles, email addresses, errors, and missing optional values must wrap or collapse intentionally.

## Workflow preservation

Visual implementation MUST NOT add a new workflow, change route behavior, alter persisted data, or invent missing Vault CRUD endpoints. Existing Django tests and repeatable UI checks are the verification authority, followed by human visual approval.
