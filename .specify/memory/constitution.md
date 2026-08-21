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

### II. The Entire Codebase Is Agent-Accessible
There are no human-only zones in this repository. Autonomous agents may
read and write any path. Sensitive decisions are governed by the factory's
policy layer and HITL approval gates — not by zone restrictions in this
constitution.

<!-- If your project has sensitive paths (auth, payments, PII), replace
     Principle II with zone definitions and add a SECURITY_ZONES.md.
     Example:
     ### II. Security Zones
     `src/auth/` and `src/payments/` are sensitive zones. Agent writes to
     these paths require HITL approval. The factory enforces this via
     SECURITY_ZONES.md at the repo root. -->

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
