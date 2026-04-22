#!/usr/bin/env bash
set -euo pipefail

DB_NAME="${POSTGRES_DB:-photo_curator}"
DB_USER="${POSTGRES_USER:-photo_curator}"

# Ensure migration tracking table exists.
psql -v ON_ERROR_STOP=1 -U "$DB_USER" -d "$DB_NAME" <<'SQL'
CREATE TABLE IF NOT EXISTS schema_migrations (
  version TEXT PRIMARY KEY,
  applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
SQL

for migration in /migrations/*.sql; do
  version="$(basename "$migration")"
  already_applied="$(psql -tA -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1 FROM schema_migrations WHERE version = '$version' LIMIT 1;")"
  if [[ "$already_applied" == "1" ]]; then
    echo "[skip] $version already applied"
    continue
  fi

  echo "[apply] $version"
  psql -v ON_ERROR_STOP=1 -U "$DB_USER" -d "$DB_NAME" -f "$migration"
  psql -v ON_ERROR_STOP=1 -U "$DB_USER" -d "$DB_NAME" -c "INSERT INTO schema_migrations(version) VALUES ('$version');"
done

echo "Migrations complete."
