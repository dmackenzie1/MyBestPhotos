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
- Compose mounts `PHOTO_ROOT_1..3`.
- Python runner consumes `PHOTO_ROOTS_JSON` and stores `source_root + relative_path`.

## Future ideas
- Add semantic search only if full-text + structured filters are insufficient.
- Add optional websocket updates for long-running ingestion progress.
