# darkfactory-project-template

Make any repository workable by [AgentDarkFactory](https://github.com/aitronixsolutions/darkfactory):
a Jira ticket goes in; a governed, human-approved, evidence-attested pull
request comes out. This template ships the **governance core** every
project needs, plus **stack overlays** for build/test/evidence wiring.

Template version: see [`TEMPLATE_VERSION`](TEMPLATE_VERSION) ·
changes between versions: [`CHANGELOG.md`](CHANGELOG.md) ·
the authoritative factory contract: `docs/TARGET-REPO-CONTRACT.md` in the
darkfactory repo.

## Layout

| Path | Purpose |
|---|---|
| `.opencode/agents/` | The four governed agents the factory invokes **by exact name**: `spec`, `adf-plan`, `dev`, `review`. Edit their *prompts* freely; their `permission:`/`model:` lines are overridden by the factory's platform floor |
| `.opencode/commands/` | Spec Kit commands (the plan phase runs `speckit.plan`) |
| `.specify/` | Spec Kit templates, constitution, and the bash scripts the plan agent is allowed to run (`.specify/scripts/bash/*` is its entire shell allowlist) |
| `SECURITY_ZONES.md` | Your agent-forbidden paths — read it; enforcement is factory-side |
| `specs/` | The factory writes `specs/<TICKET-KEY>/spec.md` + `plan.md` per ticket |
| `security/` | The factory writes `trivy-report.md` + `sbom.cdx.json` per run |
| `overlays/` | Stack wiring — [apply one](overlays/README.md) (Node is fully supported today) |
| `scripts/verify-factory-contract.mjs` | Run any time: does this repo still satisfy the factory contract? |

## Setup

1. **Copy the core** (everything except `overlays/`) into your repo — or
   start from this repo directly.
2. **Apply your stack overlay**: copy `overlays/node/`'s contents over the
   repo root (paths mirror the root). See [`overlays/README.md`](overlays/README.md).
   No overlay for your stack yet? Read the honest notes in
   [`overlays/python/README.md`](overlays/python/README.md) before proceeding.
3. **Personalize**: `{{project_name}}` and `{{ratification_date}}` in
   `.specify/memory/constitution.md`; your paths in `SECURITY_ZONES.md`
   and `.github/CODEOWNERS`; the sample `src/lib` module.
4. **Register with the factory** (factory-side, not in this repo):
   - Point a floor's `FACTORY_TARGET_REPO` (or the floor's sources) at
     this repo; set `JIRA_PROJECT` to your board's key.
   - **Mirror your `SECURITY_ZONES.md` rows into the factory's zone map**
     (`agentguard/policies/zones/zones-v0.json` or `FACTORY_ZONES`).
     Skipping this leaves the factory's default zones in force, not
     yours. Zone names must be `payments`, `auth`, or `pii` today.
5. **Branch rules**: default branch `main` (the factory's PRs target it);
   allow force-push on `factory/*` branches (factory-owned namespace);
   do **not** require signed commits (delivery commits host-side);
   protect `main` with the CI check + human review — the factory's own
   `docs/BRANCH-PROTECTION.md` has the full checklist.
6. **Verify**: `node scripts/verify-factory-contract.mjs` — green means
   the factory can work this repo.

## The contract, in one minute

- **Install/test**: the factory runs `npm ci` then `npm test` under a
  600s cap in an offline sandbox that reaches **registry.npmjs.org
  only** — a lockfile is mandatory, and no dependency may fetch from
  another host at install time (no browser downloads, prebuilt-binary
  fetches from GitHub Releases, `git:` specifiers, private registries).
- **Evidence tiers** (optional, repo-declared): `test:factory` writing
  `test-results/vitest.json` feeds the console's test-report card;
  `test:ui` (Playwright — see [`overlays/node/PLAYWRIGHT.md`](overlays/node/PLAYWRIGHT.md))
  adds per-test videos. `test-results/` stays gitignored: the factory
  reads it from the workspace, and delivery stages the whole worktree.
- **No supported stack manifest** (e.g. no `package.json`): agents still
  work the repo, but nothing installs and no tests run — the factory
  marks such tickets **UNVERIFIED** on the PR and the approval card.
- **The factory writes** `specs/<KEY>/`, `security/`, and commits to
  `factory/<KEY>` branches as `AgentDarkFactory`; a spec-only change is
  a failed ticket (agents must change code).
- **Line endings**: scripts stay LF (`.gitattributes` enforces it) —
  CRLF breaks both script execution and the dev agent's file editing.

Built on [GitHub Spec Kit](https://github.com/github/spec-kit).
