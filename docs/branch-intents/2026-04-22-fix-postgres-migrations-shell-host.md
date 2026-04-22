# Branch Intent: 2026-04-22-fix-postgres-migrations-shell-host

## Intent
- Fix compose startup so `postgres-migrations` actually applies SQL before `python-runner` inserts into `files`.

## Scope
- In scope:
  - Correct migration container command interpreter.
  - Ensure migration container connects to the `postgres` service host.
- Out of scope:
  - SQL schema content changes.
  - Python pipeline query changes.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-fix-postgres-migrations-runner-startup.md`
  - `docs/branch-intents/2026-04-22-fix-compose-connectivity-and-startup.md`
- Relevant lessons pulled forward:
  - Keep startup fixes minimal and explicit in compose.
  - Prefer deterministic gating via `service_completed_successfully` and make migration execution reliable.
- Rabbit holes to avoid this time:
  - Refactoring runner or API internals when the failure is pre-schema startup.

## Architecture decisions
- Decision:
  - Run `apply-migrations.sh` with `bash` and set `PGHOST=postgres`, `PGPORT=5432` in `postgres-migrations`.
- Why:
  - The script uses Bash syntax (`[[ ... ]]`) and must run against the DB service, not local socket defaults.
- Tradeoff:
  - Slightly more explicit env/command config in compose, but much lower startup ambiguity.

## Error log (mandatory)
- Exact error message(s):
  - `UndefinedTable: relation "files" does not exist`
  - `service "postgres-migrations" didn't complete successfully: exit 2`
- Where seen (command/log/file):
  - User-provided `docker compose up` logs for `mybestphotos-python-runner` and `mybestphotos-postgres`.
- Frequency or reproducibility notes:
  - Reproduces on fresh volumes when migrations do not execute successfully.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Verified compose used `command: ["sh", "/migrations/apply-migrations.sh"]` while script uses Bash-specific `[[ ... ]]`.
  - Why this was tried:
    - Exit code 2 strongly suggested shell parsing failure before migrations were applied.
  - Result:
    - Confirmed mismatch between script syntax and invoked shell.
- Attempt 2:
  - Change made:
    - Updated compose command to `bash` and added explicit Postgres host/port env in migration service.
  - Why this was tried:
    - Ensure script executes and resolves DB target service predictably.
  - Result:
    - Compose config now aligns with script requirements and service networking expectations.

## What went right (mandatory)
- Root cause isolated to migration service execution/runtime config, not application SQL statements.

## What went wrong (mandatory)
- Full end-to-end container validation may still depend on local Docker daemon/runtime availability.

## Validation (mandatory)
- Commands run:
  - `docker compose config`
  - `bash -n services/postgres/apply-migrations.sh`
- Observed results:
  - Compose renders with updated migration command/env.
  - Migration script passes Bash syntax check.

## Follow-up
- Next branch goals:
  - Verify fresh `docker compose up --build` creates schema and runner can insert into `files`.
- What to try next if unresolved:
  - Capture `postgres-migrations` container logs directly and add `set -x` temporarily for deeper script-level tracing.
