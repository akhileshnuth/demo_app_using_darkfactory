# Data Model: DFT-12 Visual Design Pass

This feature introduces no persisted data, API resources, migrations, or domain state. The following presentation entities are planning concepts only.

## Visual treatment

- **Fields:** semantic role, typography level, color role, spacing, surface/border treatment, interaction-state treatment, and accessibility semantics.
- **Relationships:** applied to shared shell elements, page headers, actions, forms, lists/tables, feedback, pagination, and empty states.
- **Validation rules:** equivalent controls must use the same treatment; state meaning must remain understandable without color, hover, or motion; text and essential actions must remain readable and reachable at every supported viewport.

## Primary screen

- **Fields:** existing route/template, page purpose, primary action, supporting content, feedback states, and responsive layout requirements.
- **Relationships:** consumes shared visual treatments and preserves the existing view/form/content workflow.
- **State transitions:** default → hover/focus/active/selected/disabled as applicable; normal → loading/empty/error/success feedback as already produced by the existing workflow. No new product state is introduced.

## Scope note

The existing application models (`accounts`, `checklists`, and `vault`) are unchanged. Unreachable Vault CRUD templates and route names are not made functional by this plan; they require a separate product decision.
