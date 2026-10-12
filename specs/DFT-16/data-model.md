# Data Model: DFT-16 Copyright Footer

This feature introduces no persisted data, database schema, or API resource.

## Copyright notice

- **Representation**: Static text node in `./templates/base.html`.
- **Value**: `Copyright 2026 Daylight. All rights reserved.`
- **Relationships**: Rendered once by the base layout for every child template
  that uses it.
- **Validation**: The rendered response must contain one semantic footer and
  the exact approved notice; existing page content must remain present.

## Base template

- **Representation**: Existing shared Django template at
  `./templates/base.html`.
- **Behavior**: Owns the footer placement so child views do not duplicate it.
- **State transitions**: None; the notice is static.
