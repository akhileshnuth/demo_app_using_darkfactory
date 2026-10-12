# UI Contract: Shared Copyright Footer

## Rendered layout contract

For every page rendered from `./templates/base.html`:

- The response contains exactly one semantic `<footer>` region supplied by the
  shared layout.
- The footer contains the exact visible text
  `Copyright 2026 Daylight. All rights reserved.`.
- The footer is outside the primary content region and does not replace the
  `{% block content %}` output.
- Child templates do not need to add footer markup.

Pages that do not inherit from `base.html` are outside this contract.
