# MyBestPhotos

A practical personal photo curation stack with a clear service layout and Docker Compose orchestration.

This branch is ready for local pipeline runs with:
- repeatable Docker Compose startup,
- idempotent migration execution,
- configurable ingest roots,
- optional LM Studio image descriptions for richer captions.

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
- `PHOTO_ROOT=/path/to/photos`

Set runner roots list (container paths, CSV):
- `PHOTO_INGEST_ROOTS=/photos/library`

Optional LM Studio settings (for vision-based descriptions):
- `PHOTO_CURATOR_DESCRIPTION_PROVIDER=lmstudio`
- `PHOTO_CURATOR_LMSTUDIO_BASE_URL=http://host.docker.internal:1234/v1` (or your LAN host URL)
- `PHOTO_CURATOR_LMSTUDIO_MODEL=qwen2.5-vl-7b-instruct`
- `PHOTO_CURATOR_LMSTUDIO_TIMEOUT_SECONDS=60`

> If LM Studio runs on the same host as Docker Desktop, `host.docker.internal` is the easiest path.

### 2) Start stack

```bash
docker compose up -d postgres app-server app-client nginx
```

Open UI at:
- http://localhost:8080

Direct service ports (for troubleshooting):
- API: http://localhost:3001/api/v1/health
- Client preview: http://localhost:4173
- Postgres: localhost:5432

`docker compose` now waits for Postgres health checks before starting dependent services, and waits for app health checks before wiring NGINX.

### 3) Apply database migrations

```bash
docker compose exec postgres sh -lc "/migrations/apply-migrations.sh"
```

This uses a `schema_migrations` table and applies each SQL file once in filename order.

### 4) Run ingest/scoring/description pipeline

```bash
docker compose --profile runner run --rm python-runner
```

### 5) Verify ingest and API health

```bash
docker compose logs --tail=100 app-server
curl -s http://localhost:8080/api/v1/photos | jq '.items | length'
```

## Pipeline runbook (tonight-friendly)

For long-running local processing, use this sequence:

1. `docker compose up -d postgres app-server app-client nginx`
2. `docker compose exec postgres sh -lc "/migrations/apply-migrations.sh"`
3. `docker compose --profile runner run --rm python-runner`
4. Re-run step 3 whenever new files arrive (pipeline is upsert-oriented).

### Recovery and reruns

- If a migration fails, fix SQL and re-run `apply-migrations.sh`; successful versions are recorded and skipped.
- If descriptions need regeneration, run:
  ```bash
  docker compose --profile runner run --rm python-runner \
    sh -lc "uv run --project . photo-curator describe --description-provider lmstudio --model-name qwen2.5-vl-7b-instruct"
  ```
- `pgdata` volume preserves DB state across container restarts.

## Database migration strategy

- **Baseline:** migration SQL files under `services/postgres/migrations`.
- **Execution:** `services/postgres/apply-migrations.sh` runs in-order and records applied versions.
- **For schema changes:** add a new file like `003_add_xyz.sql`, never edit already applied migration files in deployed environments.
- **For large backfills:** keep schema migration and data backfill as separate steps; run backfill from runner or one-off SQL script.


## UI screenshot capture

When you need a quick UI screenshot artifact locally:

```bash
npm install
npx playwright install --with-deps chromium
npm run screenshot:ui
```

This captures `http://localhost:8080` to `artifacts/ui-home.png` (start the stack first with `docker compose up -d postgres app-server app-client nginx`).

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

### Description providers

- `basic` (default): deterministic metadata-based captions.
- `lmstudio`: calls LM Studio OpenAI-compatible `/chat/completions` with inline image data.

Provider is selected with:
- env var `PHOTO_CURATOR_DESCRIPTION_PROVIDER`, or
- CLI `--description-provider basic|lmstudio`.

If LM Studio is unavailable, the runner logs a warning and falls back per-image to deterministic captions.

## Status UX and logging notes

- Current UI shows data refresh based on API fetches.
- Current runner logs stage progress (`discover`, `score-metrics`, `describe`) to console and `logs/`.
- WebSocket live progress is not yet implemented; recommended next step is an `/api/v1/jobs` + WS stream for in-flight pipeline status events.

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
