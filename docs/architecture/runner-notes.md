# Python Runner Notes

Runner participates in default stack startup (`docker compose up`) and is also runnable manually with:

```bash
docker compose run --rm python-runner
docker compose run --rm python-advanced-runner
```

Pipeline now has two practical passes:

1. **Base ingest**
   - discover files
   - upsert stable file truth into `files`
   - compute deterministic quality metrics into `file_metrics`
2. **Advanced runners**
   - run enrichment passes that may improve over time
   - current runner includes CLIP-based aesthetic scoring and descriptions
   - designed to be rerunnable/backfillable

Current CLI alignment:
- `photo-curator base-ingest` for canonical file ingest.
- `photo-curator score-clip-aesthetic` for standalone CLIP aesthetic backfills.
- `photo-curator advanced-runner` for CLIP aesthetic + optional description enrichment.
- `photo-curator pipeline` runs base ingest + advanced runners in one command.

## Compose runtime split

- `python-runner` container executes `photo-curator base-ingest`.
- `python-advanced-runner` container executes `photo-curator advanced-runner`.
- Advanced runner container mounts the same source photo root (`/photos/library`) and waits for
  successful completion of base ingest before running.
- GPU requirements are isolated to the production overlay (`docker-compose.prod.yml`) for
  `python-advanced-runner`.

## Environment
- Uses `uv` inside container.
- Python 3.12 image by default.
- Description provider is configurable:
  - `PHOTO_CURATOR_DESCRIPTION_PROVIDER=basic|lmstudio`
  - `PHOTO_CURATOR_LMSTUDIO_BASE_URL`
  - `PHOTO_CURATOR_LMSTUDIO_MODEL`
  - `PHOTO_CURATOR_LMSTUDIO_TIMEOUT_SECONDS`

## LM Studio integration

When provider is `lmstudio`, the description stage sends each image to LM Studio's
OpenAI-compatible `chat/completions` endpoint and stores returned captions in
`file_descriptions.description_text`.

## CLIP aesthetic scoring note

- `nima_score` is treated as advanced derived metadata, not raw file truth.
- `nima_score` is a legacy column name and currently stores CLIP-based aesthetic output.
- The VGG-16 NIMA model is not used in the active advanced runner path.
- The runner processes rows missing `nima_score` first (or all rows with `--refresh-all`)
  and records `nima_model_version` + `advanced_metadata_updated_at` for future backfills.

## GPU note
If adding PyTorch model inference later, pin CUDA/ROCm builds explicitly in docs and image tags.


## Startup/ordering

- Runner waits for both Postgres and app-server health checks in Compose.
- Runner keeps mounted photo roots and cache paths from the host.

## Runtime/GPU

- Base compose keeps runner portable without hard GPU requirements.
- GPU/prod overlay (`docker-compose.prod.yml`) sets `gpus: all` plus `NVIDIA_VISIBLE_DEVICES` and `NVIDIA_DRIVER_CAPABILITIES`.
- Ensure Docker host has NVIDIA container runtime support when using the prod GPU overlay.
- `uv` cache persists via named volume `uv-cache` to reduce repeated cold-start setup time.
