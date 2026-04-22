# Postgres Service

This directory owns database-related artifacts.

- `init/001_stock_schema.sql` (loaded on fresh volumes via docker-entrypoint-initdb.d)
- `bootstrap.sql` (idempotent schema bootstrap, runs on every startup via postgres-bootstrap service)

## Startup behavior

On a **fresh volume**, Postgres loads `init/001_stock_schema.sql` automatically during first init.

The Compose `postgres-bootstrap` service then runs `bootstrap.sql` against the running database
on every startup. Since all statements use `CREATE TABLE IF NOT EXISTS`, this is safe to run
repeatedly and ensures tables exist even on existing volumes where init scripts are skipped.

## Debug access from host CLI / AI agents

The Compose service publishes Postgres on:

- `${POSTGRES_BIND_ADDRESS:-0.0.0.0}:${POSTGRES_PUBLIC_PORT:-5432}` -> container `5432`

That means local tools (and AI debugging agents that can run shell commands) can inspect data directly.

### Recommended utilities

- `psql` (official Postgres CLI)
- `pgcli` (optional interactive CLI)
- `docker compose exec postgres psql ...` (no local install required)

### Example commands

```bash
# Check connectivity from host shell
PGPASSWORD="$POSTGRES_PASSWORD" psql \
  "host=127.0.0.1 port=${POSTGRES_PUBLIC_PORT:-5432} user=${POSTGRES_USER:-photo_curator} dbname=${POSTGRES_DB:-photo_curator}" \
  -c "select now();"

# List tables in public schema
PGPASSWORD="$POSTGRES_PASSWORD" psql \
  "host=127.0.0.1 port=${POSTGRES_PUBLIC_PORT:-5432} user=${POSTGRES_USER:-photo_curator} dbname=${POSTGRES_DB:-photo_curator}" \
  -c "\dt public.*"

# Peek at recent files rows
PGPASSWORD="$POSTGRES_PASSWORD" psql \
  "host=127.0.0.1 port=${POSTGRES_PUBLIC_PORT:-5432} user=${POSTGRES_USER:-photo_curator} dbname=${POSTGRES_DB:-photo_curator}" \
  -c "select id, path, created_at from files order by created_at desc limit 20;"

# Same thing without local psql installed
docker compose exec postgres psql \
  -U "${POSTGRES_USER:-photo_curator}" \
  -d "${POSTGRES_DB:-photo_curator}" \
  -c "select count(*) as files_count from files;"
```

> `curl` is not a fit for direct Postgres queries because Postgres speaks its own wire protocol (not HTTP). Use `psql`/`pgcli`, or query through the API endpoints if you need HTTP tooling.

### Production safety note (important)

This public port mapping is currently intended for debugging/inspection convenience.
Before production deployment, restrict Postgres exposure (for example `127.0.0.1` bind only, private network-only access, firewall rules, or removing host port publishing entirely).

## Resetting to stock schema

If you need a clean baseline DB again, remove the DB volume and restart:

```bash
docker compose down -v
docker compose up -d postgres
```
