# Template changelog

Customers: after pulling a new template version, re-run
`node scripts/verify-factory-contract.mjs` in your repo and read the
entries between your version and this one. Your current version is
whatever `TEMPLATE_VERSION` said when you copied the template.

## 0.2.0 — 2026-08-22

Restructured as a **language-agnostic governance core + opt-in stack
overlays**. Breaking relative to 0.1.x:

- `package.json` moved out of the root into `overlays/node/` — the root
  is now stack-neutral. Node projects apply the overlay (which also adds
  the lockfile 0.1.0 was missing; without one, every factory ticket
  failed at `npm ci`).
- `overlays/node` wires the behavior-evidence tiers (`test:factory` →
  `test-results/vitest.json`) that 0.1.0 omitted, plus CI, CODEOWNERS,
  a sample module + test, and a Playwright recipe (`PLAYWRIGHT.md`).
- `SECURITY_ZONES.md` added; constitution Principle II now declares
  zones by default (the "no zones" stance became an explicit, recorded
  opt-out — it was silently the default before, while the factory
  applied its own demo zone map).
- `scripts/verify-factory-contract.mjs` added — run it any time to check
  the repo still satisfies the factory contract.
- `.gitattributes` (LF for scripts), Node-aware `.gitignore`,
  MIT LICENSE, `TEMPLATE_VERSION`, this changelog.
- Removed: committed `.specify/feature.json` (runtime state — it made
  every factory PR carry a spurious diff), `speckit.taskstoissues`
  command (the factory is Jira-driven), the tests-are-optional line in
  the tasks template (contradicted constitution Principle IV).

## 0.1.0 — 2026-08-20

Initial scaffold.
