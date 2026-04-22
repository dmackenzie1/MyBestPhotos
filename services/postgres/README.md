# Postgres Service

This directory owns database-related artifacts.

- `migrations/001_init.sql` (legacy schema)
- `migrations/002_core_v1.sql` (current core schema)

Migrations run automatically via the `postgres-migrations` one-shot service during `docker compose up`.

Apply manually from compose:

```bash
docker compose run --rm postgres-migrations
```

## Migration strategy

- `apply-migrations.sh` creates `schema_migrations` if missing.
- Each `migrations/*.sql` file in `/migrations` runs once and is tracked by filename.
- Add new migrations with incrementing prefixes (for example `003_add_indexes.sql`).
