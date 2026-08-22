# Stack overlays

The template root is the **language-agnostic governance core** — every
project takes all of it. An overlay adds one stack's build/test/evidence
wiring on top.

**To apply an overlay**: copy the overlay directory's contents over your
repo root (paths mirror the root exactly), then run
`node scripts/verify-factory-contract.mjs`.

| Overlay | Status |
|---|---|
| `node/` | **Supported end-to-end** — install, tests, evidence tiers, CI |
| `python/` | Placeholder — see its README for exactly what works today |

No overlay at all is valid: the factory's agents still work the repo, but
no tests ever run, and every ticket is marked **UNVERIFIED** for the
human approver. Choose that knowingly.

Adding your own stack: mirror `node/`'s shape (manifest, one sample
module + test, CI job, evidence wiring where the factory supports it) and
check the factory's `docs/TARGET-REPO-CONTRACT.md` for what the runtime
can execute — the sandbox toolchain and egress allowlist are the binding
constraints, not this template.
