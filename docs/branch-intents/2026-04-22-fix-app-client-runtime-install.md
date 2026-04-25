# Branch Intent: fix app-client runtime install

## Quick Summary
- Purpose: Fix Docker build failure for `app-client` where the runtime stage tries to install a private workspace dependency from npm registry.
- Keywords: fix, app, client, runtime, install
## Intent
- Fix Docker build failure for `app-client` where the runtime stage tries to install a private workspace dependency from npm registry.

## Scope
- In scope:
  - Update `services/app/client/Dockerfile` runtime install strategy.
  - Record error details and attempts in this branch-intent file.
- Out of scope:
  - API/server changes.
  - Compose service renaming/port changes.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-restructure-services-stack.md`
  - `docs/branch-intents/2026-04-22-foundation-stack.md`
  - `docs/branch-intents/2026-04-22-fix-client-importmeta-env.md`
- Relevant lessons pulled forward:
  - Docker/npm validation gaps previously blocked confidence; this branch should run an actual targeted docker build.
  - Keep changes minimal and avoid broad stack rewiring.
- Rabbit holes to avoid this time:
  - Reworking workspace/package architecture just to run Vite preview.

## Architecture decisions
- Decision:
  - In app-client runtime stage, avoid using `services/app/client/package.json` and install only `vite` in a minimal `/app` package.
- Why:
  - The previous runtime `npm install --omit=dev vite` still read client dependencies (including `@mybestphotos/shared@0.1.0`) and attempted registry fetches.
- Tradeoff:
  - Runtime image no longer carries the client package metadata; it carries only what is needed to serve built static assets with Vite preview.

## Error log (mandatory)
- Exact error message(s):
  - `npm error 404 '@mybestphotos/shared@0.1.0' is not in this registry.`
  - `target app-client: failed to solve: process "/bin/sh -c npm install --omit=dev vite" did not complete successfully: exit code: 1`
- Where seen (command/log/file):
  - `docker compose up -d postgres app-server app-client nginx` build logs, `services/app/client/Dockerfile` line containing runtime `RUN npm install --omit=dev vite`.
- Frequency or reproducibility notes:
  - Reproduces consistently during `app-client` image build.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Removed `COPY package.json` from runtime stage and replaced with `npm init -y && npm install --omit=dev vite`.
  - Why this was tried:
    - Prevent npm from reading workspace dependency declarations that reference unpublished private package names.
  - Result:
    - Runtime Dockerfile updated successfully; containerized build validation blocked in this environment because `docker` CLI is unavailable.

## What went right (mandatory)
- Isolated failure to runtime-stage package install behavior.

## What went wrong (mandatory)
- Original runtime stage assumed workspace package dependencies were resolvable from public npm registry.

## Validation (mandatory)
- Commands run:
  - `docker build -f services/app/client/Dockerfile -t mybestphotos-app-client:test .`
- Observed results:
  - `docker` command is unavailable in this environment (`/bin/bash: docker: command not found`), so image build could not be executed here.

## Follow-up
- Next branch goals:
  - If needed, switch runtime server from Vite preview to a static file server with no npm install.
- What to try next if unresolved:
  - Copy prebuilt Vite CLI binaries from build stage or use nginx static serving for client assets.
