# Branch Intent: 2026-04-22-fix-files-table-missing-existing-volume

## Quick Summary
- Branch: `2026-04-22-fix-files-table-missing-existing-volume`
- Purpose: Fix compose startup failures where `python-runner` inserts into `files` before schema exists on an already-initialized Postgres volume.
- Scan first: Use this branch when you are working on the same feature area or error pattern.



## Intent
- Fix compose startup failures where `python-runner` inserts into `files` before schema exists on an already-initialized Postgres volume.

## Scope
- In scope:
  - Restore deterministic schema application on startup for existing DB volumes.
  - Gate `app-server` and `python-runner` on successful schema application.
  - Update Postgres service docs to describe startup behavior.
- Out of scope:
  - SQL schema redesign.
  - Changes to pipeline insert/query logic.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-fix-postgres-migrations-runner-startup.md`
  - `docs/branch-intents/2026-04-22-stock-schema-no-migrations.md`
  - `docs/branch-intents/2026-04-22-fix-postgres-migrations-shell-host.md`
- Relevant lessons pulled forward:
  - Postgres health checks alone do not guarantee schema readiness.
  - Existing volumes can bypass `/docker-entrypoint-initdb.d` bootstrap scripts.
  - Startup ordering must explicitly gate querying services on schema-ready state.
- Rabbit holes to avoid this time:
  - Refactoring Python pipeline internals when failure is infrastructure/startup ordering.

## Architecture decisions
- Decision:
  - Re-introduce `postgres-migrations` as a one-shot compose service and require it to complete successfully before `app-server` and `python-runner` boot.
- Why:
  - This ensures schema gets applied both on fresh volumes and on pre-existing volumes where init scripts no longer run.
- Tradeoff:
  - One additional service in compose graph; startup can fail early on migration errors, which is desired for correctness.

## Error log (mandatory)
- Exact error message(s):
  - `UndefinedTable: relation "files" does not exist`
  - `ERROR:  relation "files" does not exist at character 26`
- Where seen (command/log/file):
  - User-provided `docker compose -f docker-compose.yml -f docker-compose.prod.yml up postgres app-server app-client python-runner nginx` logs (`mybestphotos-python-runner` traceback and `mybestphotos-postgres` error lines).
- Frequency or reproducibility notes:
  - Reproducible when Postgres volume already exists and does not contain baseline schema.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Reviewed current compose wiring and confirmed only init SQL bootstrap was active (no migration runner).
  - Why this was tried:
    - Validate why startup still fails despite stock schema file being present.
  - Result:
    - Confirmed root cause: existing volumes skip init scripts, leaving schema absent.
- Attempt 2:
  - Change made:
    - Added `postgres-migrations` service with Bash execution and service host env; gated `app-server` and `python-runner` on `service_completed_successfully`.
  - Why this was tried:
    - Ensure schema is present before any inserts/queries run.
  - Result:
    - Compose startup graph now enforces schema application before dependent services.

## What went right (mandatory)
- Root cause mapped cleanly to DB lifecycle behavior (`initdb` runs once) rather than application SQL.

## What went wrong (mandatory)
- Could not run live Docker validation in this environment (`docker` binary unavailable).

## Validation (mandatory)
- Commands run:
  - `docker compose version`
  - `docker compose config`
  - `bash -n services/postgres/apply-migrations.sh`
- Observed results:
  - `docker compose version` and `docker compose config` fail in this environment with `docker: command not found`.
  - Bash syntax check passes for `apply-migrations.sh`.

## Follow-up
- Next branch goals:
  - Validate full startup and runner ingest on a Docker-enabled host.
- What to try next if unresolved:
  - Capture `postgres-migrations` container logs and confirm migration SQL reaches `schema_migrations` and `files` creation on startup.
