# Research: DFT-16 Copyright Footer

## Decision: Use a static semantic footer in the shared base template

**Decision**: Add one `<footer>` containing `Copyright 2026 Daylight. All rights
reserved.` to `./templates/base.html`, outside the overridable `shell` block.

**Rationale**: `base.html` is the common inheritance point. Authenticated pages
populate `content`, while login and signup replace `shell`; placing the footer
after the shell block covers both layout variants without page-specific
duplication. The existing `./static/css/base.css` already styles `footer` and
includes a small-viewport footer rule.

**Alternatives considered**:
- Put the footer inside `shell`: rejected because templates overriding `shell`
  would omit it.
- Add footer markup to each child template: rejected because it duplicates the
  shared behavior and violates the consistency requirement.
- Add a context processor or persisted copyright setting: rejected because the
  specification calls for static content and no data/configuration mechanism is
  needed.

## Decision: Use the repository-supported brand and current feature year

**Decision**: The approved implementation text is `Copyright 2026 Daylight. All
rights reserved.`.

**Rationale**: `Daylight` is the existing product name emitted by the base CSS,
and 2026 is the feature/specification year. The explicit wording provides the
required copyright text while remaining static and readable.

**Alternatives considered**:
- A dynamically generated year: rejected because the ticket requests static
  content and introduces unnecessary template behavior.
- `© 2026 Daylight`: rejected in favor of the explicit wording above, which is
  unambiguous in plain-text and accessibility contexts.

## Validation findings

- Representative inherited views include `./templates/dashboard/dashboard.html`
  and `./templates/registration/login.html`.
- Existing rendered HTML tests use Django `TestCase`, `self.client`, URL
  reversing, and `assertContains` in `./tests/test_visual_design.py`.
- Validation commands are `python manage.py check`,
  `python manage.py test tests.test_visual_design`, and the full
  `python manage.py test` suite.
