# Python overlay — not yet supported by the factory runtime

An honest placeholder, not a broken promise.

**What works today**: the factory's agents are language-agnostic. On a
Python repo they will read your code, write a spec and plan, and make
changes — the governance core (agents, Spec Kit, zones, content gate)
applies unchanged.

**What does NOT work yet**: the verification loop. The factory's sandbox
image ships Node only (no python/pip/pytest), its egress allowlist has no
PyPI, and its test pipeline runs `npm ci`/`npm test`. A Python repo
therefore gets **no dependency install and no test run** — and as of the
matching factory release, such tickets are marked **UNVERIFIED** on the
PR and the approval card so a human decides with eyes open (older
factories shipped them looking green, which is worse).

**When this changes**: the factory's stack-profiles roadmap (per-stack
sandbox images, repo-declared build/test commands, per-stack egress and
evidence adapters). This overlay will then gain a pyproject template,
pytest evidence wiring, and CI — and `TEMPLATE_VERSION` will say so.

Until then: you may onboard a Python repo knowingly (agent-authored
changes + human verification), or wait for the profile.
