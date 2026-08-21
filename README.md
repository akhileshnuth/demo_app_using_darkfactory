# darkfactory-project-template

Bare-minimum scaffold for onboarding a repository into an
[AgentDarkFactory](https://github.com/aitronixsolutions/darkfactory) instance.

Clone or copy this template into your target repo (or use it as the starting
point for a new one). It contains every file the factory's governed pipeline
needs and nothing more.

## What's included

| Path | Purpose |
|---|---|
| `.opencode/agents/` | Four governed agents: `spec`, `adf-plan`, `dev`, `review` |
| `.opencode/commands/` | Spec-kit slash commands wired for the factory |
| `.opencode/opencode.json` | OpenCode config (schema ref only) |
| `.specify/` | Spec Kit v0.14.2 integration — scripts, templates, workflows |
| `.specify/memory/constitution.md` | Project constitution — **edit this first** |
| `specs/` | Factory writes specs here per ticket (committed empty) |
| `security/` | Factory writes Trivy reports here per run (committed empty) |
| `package.json` | Minimal shell; replace with your real build/test setup |
| `.gitignore` | Ignores generated blobs, credentials, common artifacts |

## Setup

1. **Name your project** — replace every `{{project_name}}` placeholder:
   - `.specify/memory/constitution.md`
   - `package.json`

2. **Ratify the constitution** — open `.specify/memory/constitution.md`,
   read the principles, adjust any that don't fit your project, then update
   `{{ratification_date}}` and commit.

3. **Wire up CI** — add a GitHub Actions workflow (or equivalent) that runs
   `npm test` (or your real test command). The factory requires a named
   passing check before merging PRs.

4. **Protect `main`** — require the CI check + human review on all PRs.
   The factory delivers PRs; humans merge them.

5. **Configure the factory** — in your darkfactory `.env`, set:
   ```
   JIRA_PROJECT=<your-jira-project-key>
   FACTORY_TARGET_REPO=https://github.com/<org>/<this-repo>.git
   ```

6. **Seed tickets** — create Jira tickets in your project and move them to
   the factory's trigger status. The poller picks them up automatically.

## Merge into an existing repo

Copy the `.opencode/` and `.specify/` trees into your repo root. Merge the
`.gitignore` additions. Create `specs/` and `security/` if they don't exist.
Then follow steps 1–5 above.

## Template variables

| Variable | Where | What to set |
|---|---|---|
| `{{project_name}}` | constitution, package.json | your repo / project name |
| `{{ratification_date}}` | constitution | today's date (YYYY-MM-DD) |

## Related

- [AgentDarkFactory](https://github.com/aitronixsolutions/darkfactory) — the factory itself
- [GitHub Spec Kit](https://github.com/ejfox/github-spec-kit) — the spec pipeline
