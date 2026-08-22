# Adding the UI-evidence tier (Playwright)

Optional second evidence tier: declare a `test:ui` script and the factory
runs it after green unit tests, harvesting per-test videos into the
ticket's evidence card. Requirements are strict because the sandbox is
offline and capped:

1. `npm i -D @playwright/test` — and nothing that downloads browsers at
   install time. The sandbox reaches **registry.npmjs.org only**;
   Playwright's browser CDN is unreachable. The factory's sandbox ships
   a system Chromium and sets `PLAYWRIGHT_CHROMIUM=/usr/bin/chromium`.
2. `package.json`: `"test:ui": "playwright test"`.
3. `playwright.config.ts` must:
   - honour the system browser:
     `launchOptions: { executablePath: process.env.PLAYWRIGHT_CHROMIUM }`
   - write the JSON report the factory parses:
     `reporter: [["list"], ["json", { outputFile: "test-results/playwright.json" }]]`
   - keep videos where the harvester looks: `outputDir: "test-results/pw"`,
     `use: { video: "on" }` — a video written anywhere outside
     `test-results/` is silently dropped from evidence.
   - be self-contained: `webServer` starts YOUR app on a local port with
     `reuseExistingServer: false`; nothing outside the container is
     reachable.
4. `test-results/` stays gitignored (the core `.gitignore` already does
   this) — the factory reads it from the workspace, and delivery stages
   the whole worktree, so an unignored report puts videos in your PR.
