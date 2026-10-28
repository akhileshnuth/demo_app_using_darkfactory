# Data Model: Yarn CSS Build and Check Scripts

This feature has no persistent application data or external API payloads. Its
entities are filesystem/package-script contracts.

## CSS source set

- **Location:** `./frontend/css/*.css`
- **Fields:** relative filename, file contents, deterministic build order
- **Rules:** only `.css` files are included; `base.css` is included first; each
  source must have balanced curly braces for `lint:css` to succeed.
- **Lifecycle:** discovered → read → validated (lint) → concatenated (build).
  Read or validation failures terminate the operation with a non-zero status.

## CSS build output

- **Location:** `./frontend/dist/app.css`
- **Contents:** source CSS files joined in the defined deterministic order,
  with predictable newline separation.
- **Rules:** the parent output directory is created if necessary; filesystem
  and write errors are propagated; the existing `./static/css/base.css` is not
  modified.

## Yarn CSS scripts

- **Manifest:** `./frontend/package.json`
- **Fields:** `scripts.build:css`, `scripts.lint:css`, `scripts.verify`
- **Contract:** `build:css` invokes the Node utility in build mode;
  `lint:css` invokes its balance-check mode; `verify` runs lint first and build
  only after lint succeeds.
- **Compatibility rule:** existing fields and scripts in an already-present
  manifest remain unchanged, and no third-party dependency is introduced.
