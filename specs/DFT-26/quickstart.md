# Quickstart Validation: DFT-26

## Prerequisites

- Node.js >= 22
- npm
- The frontend package dependencies installed from its lockfile

From the repository root, install the isolated frontend tooling using the
package workflow selected during implementation. Do not rely on a global
TypeScript installation.

## Type-check validation

Run:

```bash
tsc -p frontend/tsconfig.json
```

Expected result: exit status 0 for the clean source set and no emitted
JavaScript or declaration files. To validate failure behavior, temporarily add
a deliberately invalid operation to a file under `frontend/src/**/*.js`, rerun
the command, and confirm the diagnostic names that file; remove the temporary
change afterward.

## Formatter validation

Run the frontend test command from the repository's package workflow. The test
suite must verify:

- zero and ordinary byte values;
- exact 1024-based boundaries through TB;
- fractional conversion rounded to at most two decimals with zeroes trimmed;
- values larger than TB retained in TB;
- negative and non-finite inputs throwing `RangeError`.

Expected result: all formatter tests pass and return strings suitable for direct
display, as described in [data-model.md](./data-model.md).

## Regression validation

Run the existing Django suite separately with:

```bash
python manage.py test
```

The feature is standalone: no Django template is expected to change and no
formatter caller is expected until a future UI feature identifies one.
