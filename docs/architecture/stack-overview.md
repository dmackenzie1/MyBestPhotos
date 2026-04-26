# Stack Overview

Top-level Docker Compose orchestrates:
- `services/postgres` (PostgreSQL + pgvector extension)
- `services/app/server` (Node/Express API on port 3001)
- `services/app/client` (React/Vite UI on port 4173)
- `services/nginx` (reverse proxy, publishes to port 8080)
- `python-runner` (base ingest pass via uv)
- `python-advanced-runner` (CLIP aesthetic scoring + keep_score derivation)
- `python-llm-runner` (LM Studio vision model descriptions/tags/scores + semantic embeddings)

## Service ports

| Service | Container port | Host port | Notes |
|---------|---------------|-----------|-------|
| nginx | 80 | 8080 | Reverse proxy for API + UI |
| app-server | 3001 | 3001 | Express API (stub mode via STUB_MODE env) |
| app-client | 4173 | 4173 | Vite dev server / built React app |
| postgres | 5432 | 127.0.0.1:5432 | Loopback-only for local debugging |

## Runner flow

1. **Base ingest** (`python-runner`): scans photo library, extracts EXIF data, computes base metrics (blur, brightness, contrast, entropy), stores canonical file facts in `files` table.
2. **Advanced scoring** (`python-advanced-runner`): runs CLIP-based aesthetic scoring, derives `aesthetic_score`, `keep_score`, and `clip_aesthetic_score`. Uses composition balance analysis via OpenCV. Deferred apply mode avoids row-by-row churn during large batches.
3. **LLM processing** (`python-llm-runner`): calls LM Studio vision model for per-photo descriptions, tags, aesthetic scores (0–100), wall art scores (0–100), and semantic embeddings. Results stored in `file_llm_results`.

## Ingest root wiring

- Compose mounts a single host root from `PHOTO_INGEST_ROOT` to `/photos/library`.
- Python runner scans `/photos/library` by default and stores `source_root + relative_path`.

## Optional local model endpoint

- Runner can call LM Studio over local network (`PHOTO_CURATOR_DESCRIPTION_PROVIDER=lmstudio`).
- No dedicated model-hosting container is required when LM Studio is already running on the host.
- Default: `http://host.docker.internal:1234/v1` with model `qwen2.5-vl-7b-instruct`.

## Database schema strategy

- **Fresh volumes:** `services/postgres/init/001_stock_schema.sql` loads via Postgres initdb.
- **Every startup:** `postgres-bootstrap` service runs `bootstrap.sql` (idempotent, all tables use `IF NOT EXISTS`).
- All score columns are in `file_metrics`. LLM scores are migrated from `file_llm_results` into `file_metrics.llm_aesthetic_score` and `file_metrics.llm_wall_art_score` during bootstrap.

## GPU support

GPU runtime settings are isolated in `docker-compose.prod.yml` (adds `gpus: all` and NVIDIA env defaults for `python-advanced-runner`). Use that overlay on hosts with NVIDIA container runtime support.
