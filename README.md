# MyBestPhotos

A practical personal photo curation stack with a clear service layout and Docker Compose orchestration.

## Repository layout

```text
services/
  app/
    server/   # Node + Express API (TypeScript)
    client/   # React + Vite UI (TypeScript)
  nginx/      # Reverse proxy
  postgres/   # SQL migrations
packages/
  shared/     # Shared TypeScript API contracts
src/photo_curator/  # Python runner (uv)
reference/    # Design and asset references
docs/         # Architecture and process docs
docker-compose.yml
```

## Stack

- Postgres (`services/postgres`)
- Node API (`services/app/server`)
- React client (`services/app/client`)
- NGINX (`services/nginx`)
- Python runner with `uv` (`src/photo_curator`)

## Quickstart

### 1) Environment

```bash
cp .env.example .env
```

Set your photo roots:
- `PHOTO_ROOT_1=/path/to/photosA`
- `PHOTO_ROOT_2=/path/to/photosB`
- `PHOTO_ROOT_3=/path/to/photosC` (optional)

Set runner roots list (container paths):
- `PHOTO_ROOTS_JSON=["/photos/repo1","/photos/repo2","/photos/repo3"]`

### 2) Start stack

```bash
docker compose up -d postgres app-server app-client nginx
```

Open UI at:
- http://localhost:8080

### 3) Apply database migrations

```bash
docker compose exec postgres psql -U ${POSTGRES_USER:-photo_curator} -d ${POSTGRES_DB:-photo_curator} -f /migrations/001_init.sql
docker compose exec postgres psql -U ${POSTGRES_USER:-photo_curator} -d ${POSTGRES_DB:-photo_curator} -f /migrations/002_core_v1.sql
```

### 4) Run ingest/scoring/description pipeline

```bash
docker compose --profile runner run --rm python-runner
```

## NPM wiring

Workspace scripts:

```bash
npm run build
npm run build:shared
npm run build:server
npm run build:client
npm run dev:server
npm run dev:client
```

## API stub mode (for UI-first work)

Set `STUB_MODE=true` for `app-server` and it will return deterministic mock data for:
- photo list
- detail
- labels patch
- facets
- image route

This lets frontend iteration continue even before real ingest data is available.

## Python runner and uv

Python execution uses `uv` in the runner container. Keep Python commands in this style:

```bash
uv sync --project .
uv run --project . photo-curator pipeline
```

If adding PyTorch-based models later, prefer explicit CUDA/ROCm build selection in docs and image tags.

## Required process rule

Every merge must include a branch intent document under:
- `docs/branch-intents/`

Include intent, scope, architecture decisions, what went right, what went wrong, validation, and follow-ups.

## References

- `reference/README.md`
- Place inspiration screenshot as `reference/ui-inspiration.png`

## What else should we do next?

1. Add server-side pagination totals and richer facets.
2. Add category extraction into `description_json` for stronger filters.
3. Add e2e smoke checks for `docker compose up` + API health + one pipeline run.
4. Add UI screenshot artifacts in CI for visual regressions.
5. Add optional semantic search only after FTS limits are observed.
