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

## GPU note
If adding PyTorch model inference later, pin CUDA/ROCm builds explicitly in docs and image tags.
