# Branch Intent: 2026-04-22-postgres-debug-cli-access

## Quick Summary
- Purpose: Support temporary debugging workflows by making Postgres host CLI access explicit and documenting exactly how AI agents/operators should inspect data.
- Keywords: postgres, debug, cli, access
## Intent
- Support temporary debugging workflows by making Postgres host CLI access explicit and documenting exactly how AI agents/operators should inspect data.

## Scope
- In scope:
  - Confirm/standardize Compose Postgres published-port configuration for host access.
  - Document practical DB inspection commands (`psql`, `docker compose exec`) for agent usage.
  - Record production risk note that this host DB exposure must be hardened before release.
- Out of scope:
  - Schema changes.
  - API behavior changes.
  - Authentication model redesign.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-fix-postgres-migrations-password-auth.md`
  - `docs/branch-intents/2026-04-22-fix-postgres-migrations-shell-host.md`
  - `docs/branch-intents/2026-04-22-ingest-consistency-and-db-lifecycle.md`
- Relevant lessons pulled forward:
  - Keep DB-related changes compose/doc-focused and avoid unnecessary service refactors.
  - Make runtime env assumptions explicit in docs to reduce startup/debug ambiguity.
- Rabbit holes to avoid this time:
  - Avoid introducing new DB tooling dependencies or changing app query code for a docs/config request.

## Architecture decisions
- Decision:
  - Keep fixed host port `5432`, and only parameterize bind address via `POSTGRES_BIND_ADDRESS` (defaulting to `127.0.0.1`) in Compose.
- Why:
  - Preserves straightforward local CLI access while avoiding unnecessary public-port env indirection.
- Tradeoff:
  - Simpler config and safer default (loopback), but LAN-wide debugging now requires explicit bind-address override.

## Error log (mandatory)
- Exact error message(s):
  - None (feature/documentation request, not failure remediation).
- Where seen (command/log/file):
  - N/A.
- Frequency or reproducibility notes:
  - N/A.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Updated `docker-compose.yml` Postgres ports mapping to use env-driven bind address/public port.
  - Why this was tried:
    - User requested explicit public exposure for command-line and agent access.
  - Result:
    - Postgres host mapping is now explicit/configurable by env vars.
- Attempt 2:
  - Change made:
    - Added DB inspection runbook snippets in Postgres/root docs and noted production hardening requirement.
  - Why this was tried:
    - User requested instructions for debugging agents and explicit note that current posture is temporary before production.
  - Result:
    - Operators/agents now have copy-paste commands and a clear production warning.
- Attempt 3:
  - Change made:
    - Simplified prior patch based on review feedback: removed `POSTGRES_PUBLIC_PORT`, switched default bind to loopback, and trimmed extra protocol commentary from docs.
  - Why this was tried:
    - User requested leaner docs/config and confirmed fixed `5432` is enough.
  - Result:
    - Compose + docs now match the requested simpler posture.

## What went right (mandatory)
- Kept changes minimal and centered on Compose/docs.

## What went wrong (mandatory)
- Could not run live `docker compose` validation in this environment due missing Docker daemon/CLI support.

## Validation (mandatory)
- Commands run:
  - `git diff -- docker-compose.yml .env.example services/postgres/README.md README.md AGENTS.md CHANGELOG.md docs/branch-intents/2026-04-22-postgres-debug-cli-access.md`
- Observed results:
  - Confirmed compose/env/docs/changelog changes reflect requested debug-access behavior and production-risk notation.

## Follow-up
- Next branch goals:
  - Add a production override compose profile that binds Postgres to loopback or removes host publish entirely.
- What to try next if unresolved:
  - If local CLI access still fails, verify `.env` values and run `docker compose ps` plus `docker compose logs postgres` for port/listener confirmation.
