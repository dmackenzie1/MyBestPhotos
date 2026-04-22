# Postgres Service

This directory owns database-related artifacts.

- `migrations/001_init.sql` (legacy schema)
- `migrations/002_core_v1.sql` (current core schema)

Apply from compose:

```bash
docker compose exec postgres sh -lc "/migrations/apply-migrations.sh"
```

## Migration strategy

- `apply-migrations.sh` creates `schema_migrations` if missing.
- Each `*.sql` file in `/migrations` runs once and is tracked by filename.
- Add new migrations with incrementing prefixes (for example `003_add_indexes.sql`).
