# Python Runner Notes

Runner participates in default stack startup (`docker compose up`) and is also runnable manually with:

```bash
docker compose run --rm python-runner
```

Stages:
1. discover files
2. score deterministic metrics
3. generate descriptions

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
