# Branch Intent: fix postgres migrations runner startup

## Quick Summary
- Purpose: Fix pipeline startup failure where the Python runner writes to `files` before migrations are applied.
- Keywords: fix, postgres, migrations, runner, startup
## Intent
- Fix pipeline startup failure where the Python runner writes to `files` before migrations are applied.

## Scope
- In scope:
  - Ensure migrations are runnable from Docker Compose with correct mount paths.
  - Ensure app-server and python-runner wait until migrations finish successfully.
  - Update Postgres README usage to match compose wiring.
- Out of scope:
  - SQL schema changes.
  - Pipeline logic changes.
  - UI/API feature changes.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-foundation-stack.md`
  - `docs/branch-intents/2026-04-22-fix-compose-connectivity-and-startup.md`
  - `docs/branch-intents/2026-04-22-python-runner-startup-gpu-cache.md`
- Relevant lessons pulled forward:
  - Keep stack wiring changes explicit and minimal.
  - Use compose dependency conditions for startup ordering.
  - Update docs whenever startup behavior changes.
- Rabbit holes to avoid this time:
  - Refactoring pipeline internals or API routes.

## Architecture decisions
- Decision:
  - Add a one-shot `postgres-migrations` compose service that runs `apply-migrations.sh`, and gate dependent services on its successful completion.
- Why:
  - Postgres health alone does not guarantee schema readiness.
- Tradeoff:
  - Startup adds one more compose service and can fail early if migration scripts are broken, which is acceptable for safer boot behavior.

## Error log (mandatory)
- Exact error message(s):
  - `UndefinedTable: relation "files" does not exist`
  - `ERROR:  relation "files" does not exist at character 26`
- Where seen (command/log/file):
  - User-provided `mybestphotos-python-runner` traceback and `mybestphotos-postgres` logs during compose startup.
- Frequency or reproducibility notes:
  - Reproduces when runner starts against a DB that has not had migrations applied.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Audited compose and postgres scripts; found `/migrations` mount only included SQL files, while `apply-migrations.sh` lived outside that mount.
  - Why this was tried:
    - Validate whether documented migration command path could work in-container.
  - Result:
    - Confirmed script path mismatch and missing migration step in startup graph.
- Attempt 2:
  - Change made:
    - Added `postgres-migrations` one-shot service, mounted `services/postgres` to `/migrations`, and updated service dependencies to `service_completed_successfully`.
  - Why this was tried:
    - Ensure schema readiness before app-server and runner execute queries.
  - Result:
    - Compose graph now enforces migrations before querying services.

## What went right (mandatory)
- Root cause was isolated to startup ordering/schema readiness, not SQL correctness.

## What went wrong (mandatory)
- Could not perform live end-to-end container startup validation in this environment if Docker daemon access is unavailable.

## Validation (mandatory)
- Commands run:
  - `docker compose config`
  - `bash -n services/postgres/apply-migrations.sh`
- Observed results:
  - `docker compose config` could not run in this environment (`docker: command not found`).
  - Bash syntax check passed for `apply-migrations.sh`.

## Follow-up
- Next branch goals:
  - Run full compose startup on a Docker-enabled host and confirm runner completes ingest.
- What to try next if unresolved:
  - If migration container ordering still races, gate NGINX/client on app-server and keep runner explicitly profile-gated for manual trigger.
