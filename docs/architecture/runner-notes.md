# Python Runner Notes

Runner is executed with:

```bash
docker compose --profile runner run --rm python-runner
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
