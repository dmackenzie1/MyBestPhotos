# Postgres Service

This directory owns database-related artifacts.

- `migrations/001_init.sql` (legacy schema)
- `migrations/002_core_v1.sql` (current core schema)

Apply from compose:

```bash
docker compose exec postgres psql -U ${POSTGRES_USER:-photo_curator} -d ${POSTGRES_DB:-photo_curator} -f /migrations/001_init.sql
docker compose exec postgres psql -U ${POSTGRES_USER:-photo_curator} -d ${POSTGRES_DB:-photo_curator} -f /migrations/002_core_v1.sql
```
