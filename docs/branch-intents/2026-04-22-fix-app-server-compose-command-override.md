# Branch Intent: fix app-server compose command override

## Quick Summary
- Branch: `fix app-server compose command override`
- Purpose: Prevent `app-server` from crashing on startup when an older locally cached image still has an outdated default CMD that points at `/app/dist/index.js`.
- Scan first: Use this branch when you are working on the same feature area or error pattern.



## Intent
- Prevent `app-server` from crashing on startup when an older locally cached image still has an outdated default CMD that points at `/app/dist/index.js`.

## Scope
- In scope:
  - Add an explicit `app-server` command override in `docker-compose.yml` to run the known compiled entrypoint path.
  - Validate compose configuration after the change.
- Out of scope:
  - Reworking TypeScript build output structure.
  - Any API route or database changes.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-fix-compose-connectivity-and-startup.md`
  - `docs/branch-intents/2026-04-22-restructure-services-stack.md`
  - `docs/branch-intents/2026-04-22-fix-app-client-runtime-install.md`
- Relevant lessons pulled forward:
  - Keep startup fixes minimal and focused on service wiring.
  - Validate path assumptions against real build output.
- Rabbit holes to avoid this time:
  - Broad stack refactors or proxy rewrites unrelated to the startup crash.

## Architecture decisions
- Decision:
  - Set `app-server` compose `command` explicitly to `node dist/services/app/server/src/index.js`.
- Why:
  - Compose-level command override applies immediately even with previously built images that still carry an old Docker `CMD`.
- Tradeoff:
  - Duplicates entrypoint path in both Dockerfile and compose; this is acceptable for local-dev resilience.

## Error log (mandatory)
- Exact error message(s):
  - `Error: Cannot find module '/app/dist/index.js'`
- Where seen (command/log/file):
  - User-provided output from `docker compose up postgres app-server app-client nginx`.
- Frequency or reproducibility notes:
  - Reproduces when running compose against stale local app-server image metadata.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Confirmed server build output path remains `dist/services/app/server/src/index.js`.
  - Why this was tried:
    - To ensure the compose override targets an existing runtime artifact.
  - Result:
    - Path exists in local workspace build output.
- Attempt 2:
  - Change made:
    - Added explicit `command` override for `app-server` in `docker-compose.yml`.
  - Why this was tried:
    - To bypass stale image default CMD values without requiring users to remember `--build`.
  - Result:
    - Compose config renders successfully with the override in place.

## What went right (mandatory)
- The fix is low-risk and localized to compose wiring.

## What went wrong (mandatory)
- Could not run Docker containers end-to-end in this environment because Docker daemon access is unavailable.

## Validation (mandatory)
- Commands run:
  - `npm run -w services/app/server build`
  - `find services/app/server/dist -maxdepth 5 -type f | sort`
  - `docker compose config`
- Observed results:
  - Build succeeded and emitted `dist/services/app/server/src/index.js`.
  - Compose configuration validated successfully.

## Follow-up
- Next branch goals:
  - Verify user can restart with `docker compose up` (or `docker compose up --build`) and keep app-server healthy.
- What to try next if unresolved:
  - If the command override does not resolve startup, force-rebuild server image and inspect in-container `/app/dist` contents.
