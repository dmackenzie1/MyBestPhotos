# Postgres Service

This directory owns database-related artifacts.

- `init/001_stock_schema.sql` (current baseline schema loaded on first DB init)
- `migrations/001_init.sql` (legacy schema reference)
- `migrations/002_core_v1.sql` (legacy migration-era schema reference)

## Startup behavior

The Compose `postgres` service mounts `init/001_stock_schema.sql` into
`/docker-entrypoint-initdb.d/` so a fresh volume is initialized with the stock schema automatically.

This initialization runs only when the Postgres data directory is empty.

## Resetting to stock schema

If you need a clean baseline DB again, remove the DB volume and restart:

```bash
docker compose down -v
docker compose up -d postgres
```
