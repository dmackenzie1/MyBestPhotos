# Stack Overview

Top-level Docker Compose orchestrates:
- `services/postgres` (metadata store)
- `services/app/server` (Node API)
- `services/app/client` (React UI)
- `services/nginx` (reverse proxy)
- `python-runner` utility container (ingestion pipeline)

## Why this structure
- Keeps API/client together under `services/app`.
- Keeps infra concerns separate in `services/nginx` and `services/postgres`.
- Uses a runner profile for periodic ingestion jobs without always-on worker complexity.

## Multi-root support
- Compose mounts a single host root from `PHOTO_ROOT` to `/photos/library`.
- Python runner consumes `PHOTO_INGEST_ROOTS` (CSV, default `/photos/library`) and stores `source_root + relative_path`.

## Optional local model endpoint
- Runner can call LM Studio over local network (`PHOTO_CURATOR_DESCRIPTION_PROVIDER=lmstudio`).
- No dedicated model-hosting container is required when LM Studio is already running on the host.

## Future ideas
- Add semantic search only if full-text + structured filters are insufficient.
- Add optional websocket updates for long-running ingestion progress.
