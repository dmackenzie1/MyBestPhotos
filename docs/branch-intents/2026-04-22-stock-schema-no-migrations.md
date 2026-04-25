# Branch Intent: 2026-04-22-stock-schema-no-migrations

## Quick Summary
- Branch: `2026-04-22-stock-schema-no-migrations`
- Purpose: Remove migration orchestration and use a single stock schema bootstrap for fresh local environments.
- Scan first: Use this branch when you are working on the same feature area or error pattern.



## Intent
- Remove migration orchestration and use a single stock schema bootstrap for fresh local environments.

## Scope
- In scope:
  - Compose wiring for schema bootstrap without `postgres-migrations`.
  - Add a stock schema SQL file for Postgres init.
  - Update Postgres/root docs to reflect reset/bootstrap workflow.
- Out of scope:
  - Application query changes.
  - Production migration/versioning strategy.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-fix-postgres-migrations-runner-startup.md`
  - `docs/branch-intents/2026-04-22-fix-postgres-migrations-shell-host.md`
  - `docs/branch-intents/2026-04-22-ingest-consistency-and-db-lifecycle.md`
- Relevant lessons pulled forward:
  - Keep DB startup changes explicit and simple in Compose.
  - Update docs in lockstep with wiring changes.
- Rabbit holes to avoid this time:
  - Refactoring runtime codepaths unrelated to DB bootstrap.

## Architecture decisions
- Decision:
  - Use Docker Postgres `docker-entrypoint-initdb.d` bootstrap with one stock schema SQL file.
- Why:
  - Local DB is disposable and not populated; migration history adds unnecessary complexity.
- Tradeoff:
  - Re-bootstrap now requires volume reset for schema changes.

## Error log (mandatory)
- Exact error message(s):
  - None for this branch; user-directed simplification.
- Where seen (command/log/file):
  - N/A.
- Frequency or reproducibility notes:
  - N/A.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Removed `postgres-migrations` one-shot service and migration dependency gates from Compose.
  - Why this was tried:
    - Ensure startup uses stock-schema bootstrap path only.
  - Result:
    - Successful; dependent services now wait only on Postgres health and app health.
- Attempt 2:
  - Change made:
    - Added `services/postgres/init/001_stock_schema.sql` and mounted it to `/docker-entrypoint-initdb.d`.
  - Why this was tried:
    - Provide deterministic schema creation on fresh volumes with no migration runner.
  - Result:
    - Successful; schema bootstrap is now built into Postgres container init behavior.
- Attempt 3:
  - Change made:
    - Updated README docs to replace migration workflow with stock bootstrap/reset instructions.
  - Why this was tried:
    - Keep operator instructions aligned with Compose behavior.
  - Result:
    - Successful; docs now describe schema bootstrap and `down -v` reset flow.

## What went right (mandatory)
- Changes stayed tightly scoped to Compose + SQL bootstrap + docs.

## What went wrong (mandatory)
- End-to-end runtime validation is limited in this environment without a Docker daemon.

## Validation (mandatory)
- Commands run:
  - `docker compose config`
  - `bash -n services/postgres/apply-migrations.sh`
- Observed results:
  - `docker compose config` could not run (`docker: command not found`).
  - Bash syntax check passed (script retained as legacy reference, not active path).

## Follow-up
- Next branch goals:
  - Remove or archive legacy migration artifacts once no longer needed for reference.
- What to try next if unresolved:
  - Validate clean bootstrap on Docker-enabled host with `docker compose down -v && docker compose up -d`.
