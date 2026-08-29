#!/usr/bin/env node
// Does this repo still satisfy the lightspeed target-repo contract?
// Zero dependencies; run any time (CI runs it on every PR). Checks are
// derived from the factory's own source — see docs/TARGET-REPO-CONTRACT.md
// in the lightspeed repo for the authoritative list.
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

const root = process.cwd();
const problems = [];
const warnings = [];

const ok = (label) => console.log(`  ok  ${label}`);
const fail = (label, why) => problems.push(`${label} — ${why}`);
const warn = (label, why) => warnings.push(`${label} — ${why}`);

// ── governance core ───────────────────────────────────────────────────
for (const agent of ["spec", "adf-plan", "dev", "review"]) {
  const file = join(root, ".opencode", "agents", `${agent}.md`);
  if (existsSync(file)) ok(`.opencode/agents/${agent}.md`);
  else fail(`.opencode/agents/${agent}.md`, "missing — the factory invokes this agent by exact name");
}
if (existsSync(join(root, ".opencode", "agents", "plan.md"))) {
  fail(".opencode/agents/plan.md", "must not exist: `plan` collides with opencode's built-in read-only " +
    "agent, which silently loses its write tool. The factory's plan agent is `adf-plan`.");
}
if (existsSync(join(root, ".opencode", "commands", "speckit.plan.md"))) ok(".opencode/commands/speckit.plan.md");
else fail(".opencode/commands/speckit.plan.md", "missing — the plan phase runs `--command speckit.plan`");

const setupPlan = join(root, ".specify", "scripts", "bash", "setup-plan.sh");
if (existsSync(setupPlan)) {
  const body = readFileSync(setupPlan, "utf8");
  if (body.includes("--json")) ok(".specify/scripts/bash/setup-plan.sh (--json capable)");
  else fail("setup-plan.sh", "must accept --json and emit a line containing IMPL_PLAN");
} else {
  fail(".specify/scripts/bash/setup-plan.sh", "missing — the plan phase runs it before the agent");
}

// LF discipline: CRLF scripts fail inside the Linux sandbox.
const scriptsDir = join(root, ".specify", "scripts", "bash");
if (existsSync(scriptsDir)) {
  const crlf = readdirSync(scriptsDir).filter((f) => {
    const p = join(scriptsDir, f);
    return statSync(p).isFile() && readFileSync(p).includes("\r\n");
  });
  if (crlf.length) fail("LF line endings", `CRLF found in: ${crlf.join(", ")} (check .gitattributes and your git autocrlf setting)`);
  else ok("scripts are LF");
}
if (existsSync(join(root, ".gitattributes"))) {
  const attrs = readFileSync(join(root, ".gitattributes"), "utf8");
  if (attrs.includes("eol=lf")) ok(".gitattributes pins LF");
  else warn(".gitattributes", "no eol=lf rule — Windows contributors may commit CRLF scripts");
} else warn(".gitattributes", "missing — Windows contributors may commit CRLF scripts");

// Runtime outputs must never reach a PR (delivery stages the whole worktree).
const gitignore = existsSync(join(root, ".gitignore")) ? readFileSync(join(root, ".gitignore"), "utf8") : "";
for (const entry of ["test-results", "node_modules", ".specify/feature.json"]) {
  if (gitignore.includes(entry)) ok(`.gitignore covers ${entry}`);
  else fail(".gitignore", `must cover ${entry} — delivery stages the whole worktree into the PR`);
}

for (const dir of ["specs", "security"]) {
  if (existsSync(join(root, dir))) ok(`${dir}/ exists`);
  else fail(`${dir}/`, "missing — the factory writes here (specs, Trivy report, SBOM)");
}
if (!existsSync(join(root, "SECURITY_ZONES.md"))) {
  warn("SECURITY_ZONES.md", "missing — if that is deliberate, the constitution must record the no-zones decision");
}

// ── node overlay (only when a package.json exists) ────────────────────
const pkgPath = join(root, "package.json");
if (existsSync(pkgPath)) {
  const pkg = JSON.parse(readFileSync(pkgPath, "utf8"));
  if (/[{}]/.test(pkg.name ?? "")) fail("package.json name", `"${pkg.name}" is not a valid npm name (unedited template placeholder?)`);
  else ok(`package.json name "${pkg.name}"`);
  if (existsSync(join(root, "package-lock.json"))) ok("package-lock.json present");
  else fail("package-lock.json", "missing — the factory runs `npm ci`, which requires a lockfile; every ticket fails without it");
  if (pkg.scripts?.test) ok("npm test script");
  else fail("scripts.test", "missing — the factory gates changes on `npm test`");
  const tf = pkg.scripts?.["test:factory"] ?? "";
  if (!tf) warn("scripts[test:factory]", "not declared — tickets run but ship NO behavior evidence to the console");
  else if (tf.includes("test-results/vitest.json")) ok("test:factory writes test-results/vitest.json");
  else fail("scripts[test:factory]", "must write the JSON report to test-results/vitest.json — the factory reads exactly that path");
} else {
  warn("package.json", "absent — a supported-stack manifest is missing, so the factory runs NO install and NO tests; " +
    "tickets are marked UNVERIFIED for the human approver. Apply a stack overlay unless this is deliberate.");
}

// ── report ────────────────────────────────────────────────────────────
if (warnings.length) {
  console.log("\nwarnings:");
  for (const w of warnings) console.log(`  !   ${w}`);
}
if (problems.length) {
  console.error("\nCONTRACT VIOLATIONS:");
  for (const p of problems) console.error(`  x   ${p}`);
  process.exit(1);
}
console.log(`\ncontract satisfied (${warnings.length} warning${warnings.length === 1 ? "" : "s"})`);
