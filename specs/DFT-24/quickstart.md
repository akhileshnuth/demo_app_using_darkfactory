# Quickstart Validation: DFT-24

## Prerequisites

- Node.js 22 or newer, matching the repository's Node overlay requirement.
- Yarn available on `PATH`.
- A checkout containing `./frontend/package.json` and at least
  `./frontend/css/base.css`.

## Validate the package-script interface

From the repository root:

```sh
yarn --cwd frontend run
```

Expected result: the script listing includes `build:css`, `lint:css`, and
`verify`, while existing package scripts remain available.

## Validate a successful check and build

```sh
yarn --cwd frontend lint:css
yarn --cwd frontend build:css
test -f frontend/dist/app.css
yarn --cwd frontend verify
```

Expected result: each command exits successfully, `verify` performs the check
before the build, and `./frontend/dist/app.css` contains the ordered CSS from
`./frontend/css/`.

## Validate failure propagation

In a temporary working copy of a CSS source, add an unmatched `{` or `}` and
run:

```sh
yarn --cwd frontend lint:css
```

Expected result: the command exits non-zero and identifies the invalid source
file and brace problem. Running `verify` with the same input must not proceed
to a successful build. Restore the temporary source afterward.

The entity locations and validation rules are defined in
[`data-model.md`](./data-model.md); implementation-specific details belong in
the later task and implementation phases.
