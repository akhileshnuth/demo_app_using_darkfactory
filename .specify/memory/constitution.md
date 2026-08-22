# {{project_name}} Constitution

The non-negotiable principles every agent and spec for this repo must
respect. Authored for the AgentDarkFactory governed pipeline.

Replace `{{project_name}}` with your repo name and fill in the principles
that reflect your project's actual constraints. Delete these instructions
when done.

## Core Principles

### I. Spec-Kit When Used Must Be Complete
Spec-based work is optional — tickets may flow through the factory without
a formal spec. When a spec IS used, the full pipeline is mandatory:
Specify → (Clarify ↔ user) → Plan → Tasks → (Analyze ↔ user) →
Implement ↔ Converge → Done. Partial pipelines are not valid; a spec
started must be finished or explicitly abandoned.

### II. Security Zones Are Declared, Never Assumed
Sensitive paths (auth, payments, PII, secrets handling) are declared in
`SECURITY_ZONES.md` at the repo root AND mirrored into the factory's zone
map (`agentguard/policies/zones/zones-v0.json`, or the `FACTORY_ZONES`
env override) — the factory enforces from ITS config, not from this repo.
Agent writes inside a zone are denied by policy and recorded; changes to
zoned paths are human work. Zone names must come from the factory's
recognized set (today: `payments`, `auth`, `pii`).

If this project genuinely has no sensitive paths, say so EXPLICITLY:
replace this principle with "This repository declares no security zones
(reviewed <date>, by <name>)" and delete `SECURITY_ZONES.md` — an empty
zone map must be a recorded decision, never a default.

### III. Human-Gated Merge (NON-NEGOTIABLE)
Every change lands as a pull request against protected `main` and cannot
merge without human review and passing CI. The factory delivers PRs;
humans merge them.

### IV. Test-First
Changes that touch functional code ship with tests. CI on the pull request
is the authority on "green", not the agent's local run.

### V. No Novel Dependencies Without Approval
New runtime dependencies require human approval; a spec that needs one is
not autonomy-eligible on its own.

## Governance

This constitution supersedes convenience. Amendments are human-gated PRs.

**Version**: 1.0.0 | **Ratified**: {{ratification_date}} | **Last Amended**: {{ratification_date}}
