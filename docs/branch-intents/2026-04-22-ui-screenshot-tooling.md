# Branch Intent: ui screenshot tooling

## Quick Summary
- Purpose: Add a repeatable way to capture a UI screenshot artifact from the running local stack.
- Keywords: ui, screenshot, tooling
## Intent
- Add a repeatable way to capture a UI screenshot artifact from the running local stack.
- Keep process compliance by including a branch intent document for this branch.

## Scope
- In scope:
  - Root npm script for screenshot capture.
  - Root Playwright dev dependency for screenshot tooling.
  - README usage guidance for screenshot capture.
  - Branch intent document under `docs/branch-intents/`.
- Out of scope:
  - CI screenshot jobs.
  - Visual regression baselines.
  - Frontend UI behavior or styling changes.

## Architecture decisions
- Decision: Use Playwright CLI from root npm scripts (`npm run screenshot:ui`) against the existing NGINX URL (`http://localhost:8080`).
- Why: It matches the current local stack entrypoint and keeps screenshot capture one-command simple for developers.
- Tradeoff: Browser binaries require an explicit install step (`npx playwright install ...`) and may be constrained by registry/network policy in locked-down environments.

## What went right (mandatory)
- The screenshot workflow is now explicit, documented, and tied to an npm script rather than ad-hoc manual steps.
- The change is additive and low-risk, with no API or schema impact.

## What went wrong (mandatory)
- Environment policy blocked npm registry access for `playwright` during install validation (HTTP 403), so end-to-end local install was not fully verifiable here.

## Validation (mandatory)
- Commands run:
  - `npm run lint`
  - `npm install` (attempted)
- Observed results:
  - Lint command completed successfully.
  - `npm install` failed in this environment due to package registry access policy (403), not due to script syntax.

## Follow-up
- Add a CI job that captures and uploads UI screenshots as artifacts when browser-capable runners are available.
- Optionally add a second script for authenticated or deep-link screenshot paths once those flows stabilize.
