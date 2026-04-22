# Branch Intent: fix compose connectivity and startup

## Intent
- Restore end-to-end local reachability for NGINX/UI/API by fixing app-server startup and tightening compose dependency readiness.

## Scope
- In scope:
  - Fix app-server container entrypoint path to compiled output.
  - Add compose health checks and dependency conditions so Postgres/API/client start in a valid order.
  - Expose app-server and app-client host ports for temporary debugging access.
  - Update README troubleshooting ports and startup behavior notes.
- Out of scope:
  - API endpoint logic changes.
  - NGINX route shape changes.
  - Database schema changes.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-foundation-stack.md`
  - `docs/branch-intents/2026-04-22-restructure-services-stack.md`
  - `docs/branch-intents/2026-04-22-fix-app-client-runtime-install.md`
- Relevant lessons pulled forward:
  - Keep stack rewiring minimal and targeted.
  - Prior iterations had validation gaps; run focused local checks for compile/output paths and compose schema.
- Rabbit holes to avoid this time:
  - Refactoring service names or replacing NGINX routing patterns.

## Architecture decisions
- Decision:
  - Keep service names and proxy targets as-is; fix server runtime path and rely on health-gated startup in compose.
- Why:
  - Reported failures indicate a startup/runtime wiring problem, not an API contract problem.
- Tradeoff:
  - Exposing `3001` and `4173` broadens local access during testing; this may be reduced again after debugging.

## Error log (mandatory)
- Exact error message(s):
  - `host not found in upstream "app server" in /etc/nginx/conf.d/default.conf:6`
  - `Error: Cannot find module '/app/dist/index.js'`
- Where seen (command/log/file):
  - User-reported NGINX logs and app-server container logs.
- Frequency or reproducibility notes:
  - Reproduces during stack startup when app-server exits immediately and NGINX starts before healthy upstreams are available.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Verified TypeScript output location for app-server; confirmed output is nested under `dist/services/app/server/src/index.js`.
  - Why this was tried:
    - To validate the module-not-found path mismatch from app-server logs.
  - Result:
    - Confirmed container command was pointing at a non-existent path.
- Attempt 2:
  - Change made:
    - Updated app-server Docker `CMD` path, added Postgres/API/client health checks, and gated `depends_on` with health conditions. Exposed app-server/client ports in compose.
  - Why this was tried:
    - To ensure services are reachable and NGINX waits for healthy upstreams.
  - Result:
    - Compose config validates, and startup sequencing is now explicit.

## What went right (mandatory)
- Root cause for app-server crash was isolated quickly via local build artifact inspection.
- Health checks aligned with user request to verify Postgres readiness before dependent services.

## What went wrong (mandatory)
- Could not run full `docker compose up` in this environment because Docker CLI/daemon are unavailable.

## Validation (mandatory)
- Commands run:
  - `npm run -w services/app/server build`
  - `find services/app/server/dist -type f | sort`
  - `docker compose config`
- Observed results:
  - Build succeeded and confirmed compiled server entrypoint path.
  - Compose file rendered successfully with updated health checks/dependency conditions.

## Follow-up
- Next branch goals:
  - Re-validate with live `docker compose up -d` on a Docker-enabled machine and confirm NGINX/API/UI reachability.
- What to try next if unresolved:
  - If health checks fail in-container, switch to `curl` probes or add lightweight wait scripts with clearer logs per service.
