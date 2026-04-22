# MyBestPhotos

A practical personal photo curation stack with a clear service layout and Docker Compose orchestration.

This branch is ready for local pipeline runs with:
- repeatable Docker Compose startup,
- stock-schema database bootstrap on fresh volumes,
- configurable ingest roots,
- optional LM Studio image descriptions for richer captions.

## Repository layout

```text
services/
  app/
    server/   # Node + Express API (TypeScript)
    client/   # React + Vite UI (TypeScript)
  nginx/      # Reverse proxy
  postgres/   # SQL schema/bootstrap assets
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

Set your single photo ingest mount:
- `PHOTO_INGEST_ROOT=/path/to/photos`

The Python runner scans that mounted path at:
- `/photos/library`

Optional LM Studio settings (for vision-based descriptions):
- `PHOTO_CURATOR_DESCRIPTION_PROVIDER=lmstudio`
- `PHOTO_CURATOR_LMSTUDIO_BASE_URL=http://192.168.10.64:1234/v1` (or your LAN host URL)
- `PHOTO_CURATOR_LMSTUDIO_MODEL=qwen3.6-35b-a3b`
- `PHOTO_CURATOR_LMSTUDIO_TIMEOUT_SECONDS=60`

Optional ingest throttles (useful for test runs on large libraries):
- `PHOTO_CURATOR_INGEST_LIMIT=200` (default; 0 means no limit)
- `PHOTO_CURATOR_INGEST_SELECTION_STRATEGY=first|random`
- `PHOTO_CURATOR_INGEST_SELECTION_SEED=42` (used when strategy is `random`)
- `PHOTO_CURATOR_DUPLICATE_CAP_PER_FILENAME_OR_SHA=2` (skip new inserts once either filename or sha256 already appears twice; existing path rows are still updated)

Compatibility aliases (also supported):
- `INGEST_FILE_LIMIT=500`
- `INGEST_SELECTION_STRATEGY=first|random|newest`

> Default uses a LAN host URL; if LM Studio runs on the same host as Docker Desktop, `host.docker.internal` is also a good option.

### 2) Start stack

```bash
# base/default stack
docker compose up -d postgres app-server app-client python-runner nginx

# prod/gpu overlay
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d postgres app-server app-client python-runner nginx
```

Open UI at:
- http://localhost:8080

Direct service ports (for troubleshooting):
- API: http://localhost:3001/api/v1/health
- Client preview: http://localhost:4173
- Postgres: `${POSTGRES_BIND_ADDRESS:-0.0.0.0}:${POSTGRES_PUBLIC_PORT:-5432}` (default: `0.0.0.0:5432`)

Postgres is intentionally published for local debugging/agent inspection in this phase. Treat this as an **outstanding production hardening item** and restrict/remove host exposure before production rollout.

`docker compose` now waits for Postgres health checks before starting dependent services, waits for app health checks before wiring NGINX, and starts `python-runner` only after both Postgres and API are healthy.

GPU note: GPU runtime settings are isolated in `docker-compose.prod.yml` (adds `gpus: all` and NVIDIA env defaults for `python-runner`). Use that overlay on hosts with NVIDIA container runtime support.

### 3) Bootstrap the stock database schema

Schema is applied automatically on every startup via two complementary mechanisms:

- **Fresh volumes:** Postgres loads `services/postgres/init/001_stock_schema.sql` during first init.
- **Existing volumes:** The `postgres-bootstrap` service runs `bootstrap.sql` (idempotent, uses `IF NOT EXISTS`) before dependent services start.

No manual step is required. If you need to force a clean re-bootstrap:

```bash
docker compose down -v
docker compose up -d postgres
```

### 4) Run ingest/scoring/description pipeline

The default stack startup already runs `python-runner` once in parallel after API/database health checks pass.

For manual reruns (for example after adding new files):

```bash
docker compose run --rm python-runner
```

### 5) Verify ingest and API health

```bash
docker compose logs --tail=100 app-server
curl -s http://localhost:8080/api/v1/photos | jq '.items | length'
```

## Pipeline runbook (tonight-friendly)

For long-running local processing, use this sequence:

1. Start base stack: `docker compose up -d postgres app-server app-client python-runner nginx` (or add `-f docker-compose.prod.yml` for GPU hosts).
2. (Optional reset) `docker compose down -v && docker compose up -d postgres` to rebuild from stock schema.
3. Watch `docker compose logs -f python-runner` for pipeline completion.
4. Re-run ingest whenever new files arrive: `docker compose run --rm python-runner` (pipeline is upsert-oriented).

### Recovery and reruns

- If schema bootstrap needs to be rerun, recreate volumes with `docker compose down -v` and start Postgres again.
- If descriptions need regeneration, run:
  ```bash
  docker compose run --rm python-runner \
    sh -lc "uv run --project . photo-curator describe --description-provider lmstudio --model-name qwen3.6-35b-a3b"

  # GPU/prod overlay variant
  docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm python-runner \
    sh -lc "uv run --project . photo-curator describe --description-provider lmstudio --model-name qwen3.6-35b-a3b"
  ```
- `pgdata` volume preserves DB state across container restarts.

## Database schema strategy

- **Fresh volumes:** `services/postgres/init/001_stock_schema.sql` loads via Postgres initdb.
- **Every startup:** `postgres-bootstrap` service runs `bootstrap.sql` (idempotent, all tables use `IF NOT EXISTS`).
- **For schema updates in this pre-production phase:** update both `init/001_stock_schema.sql` and `bootstrap.sql`, then re-bootstrap local volumes with `docker compose down -v`.
- **For large backfills:** run backfill from runner or one-off SQL script after bootstrap.

For CLI/agent DB inspection examples (`psql`, `docker compose exec`, and why `curl` is not suitable for raw Postgres), see:
- `services/postgres/README.md`

## UI screenshot capture

When you need a quick UI screenshot artifact locally:

```bash
npm install
npx playwright install --with-deps chromium
npm run screenshot:ui
```

This captures `http://localhost:8080` to `artifacts/ui-home.png` (start the stack first with `docker compose up -d postgres app-server app-client python-runner nginx`, or add `-f docker-compose.prod.yml` on GPU hosts).

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

Python execution uses `uv` in the runner container. A named Docker volume (`uv-cache`) is mounted to preserve uv download/build cache between runs for faster startup. Keep Python commands in this style:

```bash
uv sync --project .
uv run --project . photo-curator pipeline
```

For preflight diagnostics (pathing/env/network reachability) before a run:

```bash
python scripts/python_runner_doctor.py
# offline-only validation (skip TCP probes)
python scripts/python_runner_doctor.py --skip-network
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
- Current ranking defaults to a transparent `curation_score` built from technical quality + lightweight semantic relevance.
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
