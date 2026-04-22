# Branch Intent: 2026-04-22-fix-postgres-migrations-password-auth

## Intent
- Fix the `postgres-migrations` startup failure so schema migrations run successfully before dependent services start.

## Scope
- In scope:
  - Diagnose `postgres-migrations` exit behavior from compose logs.
  - Update compose migration service environment for deterministic Postgres auth.
- Out of scope:
  - SQL migration content changes.
  - Python runner or app-server query logic changes.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-fix-postgres-migrations-shell-host.md`
  - `docs/branch-intents/2026-04-22-fix-postgres-migrations-runner-startup.md`
- Relevant lessons pulled forward:
  - Keep compose fixes minimal and targeted to startup wiring.
  - Avoid touching application logic when schema bootstrap is the failing point.
- Rabbit holes to avoid this time:
  - Refactoring migration SQL files or backend code without evidence they are the root cause.

## Architecture decisions
- Decision:
  - Add `PGPASSWORD` to the `postgres-migrations` compose service environment.
- Why:
  - The migration container connects over TCP to `postgres:5432` and `psql` requires `PGPASSWORD` (or equivalent auth material) for non-interactive password auth.
- Tradeoff:
  - Slight env duplication (`POSTGRES_PASSWORD` and `PGPASSWORD`) in one service, but clearer and more reliable non-interactive migration startup.

## Error log (mandatory)
- Exact error message(s):
  - `service "postgres-migrations" didn't complete successfully: exit 2`
- Where seen (command/log/file):
  - User-provided `docker compose up` output for `mybestphotos-postgres` and compose summary line.
- Frequency or reproducibility notes:
  - Reproduces during stack startup when migration auth is not fully configured for `psql`.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Re-checked existing migration script and compose wiring (`bash` command + `PGHOST`/`PGPORT`) to verify host/shell fixes were already present.
  - Why this was tried:
    - Confirm prior known root causes were not regressed.
  - Result:
    - Found shell/host config already correct, so likely failure shifted to authentication.
- Attempt 2:
  - Change made:
    - Added `PGPASSWORD: ${POSTGRES_PASSWORD:-photo_curator}` to `postgres-migrations` environment in `docker-compose.yml`.
  - Why this was tried:
    - `psql` in non-interactive mode needs explicit password auth material when connecting to remote Postgres service over TCP.
  - Result:
    - Compose migration service now has explicit credentials for all migration `psql` calls.

## What went right (mandatory)
- Root-cause narrowing stayed focused on compose/runtime auth and avoided unnecessary service code churn.

## What went wrong (mandatory)
- Live `docker compose up` verification could not be executed in this environment due to unavailable Docker CLI/runtime.

## Validation (mandatory)
- Commands run:
  - `sed -n '1,260p' docker-compose.yml`
  - `sed -n '1,240p' services/postgres/apply-migrations.sh`
- Observed results:
  - Verified migration service now includes `PGPASSWORD`.
  - Verified migration script uses `psql` non-interactively and depends on env-based connection/auth config.

## Follow-up
- Next branch goals:
  - Validate end-to-end on Docker-enabled host with `docker compose up --build`.
- What to try next if unresolved:
  - Capture `mybestphotos-postgres-migrations` logs directly; if auth still fails, add explicit `PGUSER` and `PGDATABASE` env and print redacted effective connection vars at script start.
