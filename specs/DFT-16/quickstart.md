# Quickstart Validation: DFT-16

## Prerequisites

From the repository root, install the existing dependency set and ensure the
Django test environment is available. No new dependency is required.

## Automated validation

Run:

```bash
python manage.py check
python manage.py test tests.test_visual_design
python manage.py test
```

Expected results:

- Django reports no configuration errors.
- The targeted visual/layout tests verify the exact footer text on a
  representative authenticated page and on a page whose child template
  overrides `shell` (login), while confirming the existing main content remains.
- The full suite passes without regressions.

The rendered response contract is documented in
`./specs/DFT-16/contracts/ui.md`; static content and placement are described in
`./specs/DFT-16/data-model.md`.
