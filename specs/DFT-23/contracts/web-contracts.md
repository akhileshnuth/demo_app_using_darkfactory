# DFT-23 Web Contract

DFT-23 preserves the existing server-rendered Django interface. It adds no
routes, forms, JSON endpoints, or user-visible behavior. The full preserved
route and authorization contract is
`../../DFT-9/contracts/web-contracts.md`.

Required outcomes:

- Authenticated `GET /checklists/` resolves `Checklist` and renders the existing
  list or empty state.
- Authenticated `GET /checklists/<id>/` resolves `ChecklistItem` and renders the
  existing detail/count presentation, including zero items.
- Existing sharing, emergency, and notification routes resolve restored models
  without missing-model errors.
- No route, method, status, redirect, authorization rule, or template contract
  changes.
