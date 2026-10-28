# Research: Yarn CSS Build and Check Scripts

## Decision: Use a dedicated frontend package manifest

Add or extend `./frontend/package.json`; do not modify the repository-root
manifest or `./overlays/node/package.json`. Expose `build:css`, `lint:css`, and
`verify` as package scripts. This follows the approved clarification and keeps
the existing npm/Vitest overlay workflow unchanged.

**Alternatives considered:** adding scripts to the Node overlay or creating a
root manifest. Both would violate the clarified package boundary and could
change the repository's existing workflow.

## Decision: Implement the utility with Node built-ins only

Implement `./frontend/scripts/build-css.js` with `node:fs` and `node:path`.
Resolve source and destination paths from the script/package location rather
than the caller's current directory. Use explicit error propagation so missing
inputs, read failures, directory-creation failures, and write failures produce
a non-zero process status.

**Rationale:** the clarification prohibits third-party packages, and the
operation is small enough that a dependency-free synchronous utility is clear
and deterministic.

**Alternatives considered:** PostCSS, a CSS framework, or a shell pipeline.
They introduce dependencies or platform-specific behavior and are out of
scope.

## Decision: Build all CSS sources deterministically

Read regular `.css` files from `./frontend/css/`, sort them explicitly with a
stable filename comparator, and ensure `base.css` is first. Join contents with
a predictable newline boundary and write `./frontend/dist/app.css`. The
existing `./static/css/base.css` remains unchanged; the plan therefore adds
the frontend source copy as the package's CSS input rather than silently
switching the clarified source path.

**Rationale:** filesystem enumeration order is not a reliable build contract,
and the specification explicitly names `frontend/css/` and `frontend/css/base.css`.
The current repository has only `static/css/base.css`, so the implementation
must establish the corresponding frontend source file without changing the
template's current static asset reference.

**Alternatives considered:** consuming `./static/css` directly would contradict
the approved input path; changing templates to consume the generated artifact
would expand scope and alter existing application behavior.

## Decision: Validate balanced curly braces in lint mode

`lint:css` scans every source file before any build is attempted. It tracks
curly-brace depth, rejects an unmatched closing brace immediately, and rejects
unclosed braces at end of file. The scanner should ignore braces inside CSS
comments and quoted strings to avoid obvious false positives, and report the
file plus useful line/column context. It is a balance check, not a complete CSS
parser.

**Rationale:** this is the exact clarified acceptance rule and can be met with
standard-library code while preserving a useful non-zero failure status.

**Alternatives considered:** a full CSS parser or semantic linter would add
dependencies and validate more than the approved contract requires.

## Decision: Compose verification with short-circuiting scripts

Set `verify` to run `lint:css` followed by `build:css` using `&&`. This ensures
invalid CSS prevents output generation, while preserving the individual Yarn
entry points and their exit statuses.

**Rationale:** it directly implements the clarification and makes the command
suitable for local and CI callers.

## Repository constraints and verification approach

The repository currently has no `frontend/` directory or package manifest. The
Node overlay targets Node 22 and uses npm/Vitest, but it must remain untouched.
The constitution requires tests for functional changes, while this planning
phase must not create tests. The later implementation plan should add focused
tests for manifest exposure, deterministic ordering, brace validation (including
comments/strings), output creation, and failure propagation, using the
repository's supported test strategy without adding a dependency.
