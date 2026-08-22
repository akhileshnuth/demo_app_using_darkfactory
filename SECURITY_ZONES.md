# Security Zones

Paths in this repository that agents must never write. A change inside a
zone is human work: the factory's policy denies the write, records the
denial, and the ticket fails rather than ships.

| Path prefix | Zone name | Why it is protected |
|---|---|---|
| `src/auth` | `auth` | Authentication / session logic |
| `src/payments` | `payments` | Money movement |
| `src/customers` | `pii` | Personal data |

Replace the rows above with YOUR sensitive paths. Two rules the factory
imposes:

1. **This file is documentation — enforcement lives in the factory's
   config.** Mirror every row into the factory's zone map
   (`agentguard/policies/zones/zones-v0.json`, or the `FACTORY_ZONES`
   environment override on the worker). If you skip this step, the
   factory applies ITS defaults, not your rows.
2. **Zone names must come from the factory's recognized set** — today
   `payments`, `auth`, `pii`. A row with any other name looks configured
   but never denies.

Keep `.github/CODEOWNERS` in step with these paths so human review is
required on the same surface the agents are denied.

<!-- machine-readable: zones = src/auth:auth, src/payments:payments, src/customers:pii -->
