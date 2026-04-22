# Postgres Service

This directory owns database-related artifacts.

- `init/001_stock_schema.sql` (loaded on fresh volumes via docker-entrypoint-initdb.d)
- `bootstrap.sql` (idempotent schema bootstrap, runs on every startup via postgres-bootstrap service)

## Startup behavior

On a **fresh volume**, Postgres loads `init/001_stock_schema.sql` automatically during first init.

The Compose `postgres-bootstrap` service then runs `bootstrap.sql` against the running database
on every startup. Since all statements use `CREATE TABLE IF NOT EXISTS`, this is safe to run
repeatedly and ensures tables exist even on existing volumes where init scripts are skipped.

## Resetting to stock schema

If you need a clean baseline DB again, remove the DB volume and restart:

```bash
docker compose down -v
docker compose up -d postgres
```
