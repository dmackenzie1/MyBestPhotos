# Branch Intent: 2026-04-22-fix-docker-build-context-venv-lib64

## Quick Summary
- Branch: `2026-04-22-fix-docker-build-context-venv-lib64`
- Purpose: Fix Docker Compose build-context transfer failures on Windows caused by trying to include `.venv/lib64` in the root build context.
- Scan first: Use this branch when you are working on the same feature area or error pattern.



## Intent
- Fix Docker Compose build-context transfer failures on Windows caused by trying to include `.venv/lib64` in the root build context.

## Scope
- In scope:
  - Add root `.dockerignore` entries to exclude local virtualenv and other non-build artifacts from context transfer.
  - Record this failure and attempted fix in branch-intent docs.
- Out of scope:
  - Dockerfile refactors.
  - Compose service renaming or port/wiring changes.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-split-compose-base-and-prod-gpu-runner.md`
  - `docs/branch-intents/2026-04-22-fix-compose-connectivity-and-startup.md`
  - `docs/branch-intents/2026-04-22-fix-app-server-compose-command-override.md`
- Relevant lessons pulled forward:
  - Keep compose/build fixes minimal and localized.
  - Document exact error text and validation limits when Docker is unavailable in this environment.
- Rabbit holes to avoid this time:
  - Avoid broad stack rewiring for a build-context packaging issue.

## Architecture decisions
- Decision:
  - Add a repository-root `.dockerignore` that excludes `.venv/` and local artifact directories.
- Why:
  - `app-server` and `app-client` builds use `context: .`, so Docker tries to archive root files unless explicitly ignored.
- Tradeoff:
  - If any ignored path were needed at image build time it would have to be copied from a non-ignored location; current Dockerfiles should not rely on local `.venv` or host caches.

## Error log (mandatory)
- Exact error message(s):
  - `target app-server: failed to solve: error from sender: open D:\code\MyBestPhotos\.venv\lib64: The file cannot be accessed by the system.`
- Where seen (command/log/file):
  - User-reported output from:
    - `docker compose -f docker-compose.yml -f docker-compose.prod.yml up postgres app-server app-client python-runner nginx`
- Frequency or reproducibility notes:
  - Reproduced in user output twice with identical sender/path failure.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Confirmed `docker-compose.yml` uses root `context: .` for `app-server`, `app-client`, and `nginx`, and found no `.dockerignore` in repo.
  - Why this was tried:
    - Verify whether Docker context includes `.venv` by default and whether ignore rules already exist.
  - Result:
    - Confirmed root context is broad and no ignore file existed.
- Attempt 2:
  - Change made:
    - Added root `.dockerignore` with `.venv/` exclusion plus common local artifact excludes.
  - Why this was tried:
    - Prevent context packager from traversing inaccessible Windows virtualenv paths and reduce unnecessary context size.
  - Result:
    - Patch applied successfully.

## What went right (mandatory)
- Root cause is directly addressed at Docker context packaging boundary with a minimal, conventional fix.

## What went wrong (mandatory)
- Could not run Docker-based end-to-end confirmation in this environment if Docker CLI/daemon is unavailable.

## Validation (mandatory)
- Commands run:
  - `git diff -- .dockerignore docs/branch-intents/2026-04-22-fix-docker-build-context-venv-lib64.md`
  - `docker compose -f docker-compose.yml -f docker-compose.prod.yml config`
- Observed results:
  - Diff shows expected ignore rules and branch-intent record.
  - Compose config command should be run on the user machine with Docker access to validate merge/runtime behavior.

## Follow-up
- Next branch goals:
  - Re-run the exact user command and verify build context transfer proceeds past sender stage.
- What to try next if unresolved:
  - Add additional ignore entries for other inaccessible host paths, then inspect Docker build context details in Docker Desktop build trace.
