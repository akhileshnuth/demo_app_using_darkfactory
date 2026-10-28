# Security scan — Trivy

**5 high**

| Severity | Kind | ID | Finding | Location |
|---|---|---|---|---|
| HIGH | vuln | `CVE-2026-114141` | toml@4.3.0 → 5.0.1: toml: toml: Denial of Service via crafted array-of-tables headers | `.opencode/package-lock.json` |
| HIGH | vuln | `CVE-2026-114142` | toml@4.3.0 → 5.0.1: toml-node: Prototype pollution: parsing a TOML document can write to Object.prototype | `.opencode/package-lock.json` |
| HIGH | vuln | `CVE-2026-114143` | toml@4.3.0 → 5.0.1: toml: toml-node: Denial of Service via long dotted keys in TOML input | `.opencode/package-lock.json` |
| HIGH | vuln | `CVE-2026-114144` | toml@4.3.0 → 5.0.1: toml: toml-node: Denial of Service via unbounded integer parsing | `.opencode/package-lock.json` |
| HIGH | vuln | `CVE-2023-54404` | zod@4.1.8 → 4.6.6: zod: zod: Denial of service via unbounded array validation | `.opencode/package-lock.json` |
