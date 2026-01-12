# MyBestPhotos (Photo Curator)

Local-only photo curation pipeline for ~10,000 images. It ingests photo metadata, computes technical metrics, generates CLIP embeddings, scores aesthetics, deduplicates near-identical photos, and selects a diverse top-N set. All originals remain in place.

## Highlights
- **Local-only** processing: no runtime downloads or web calls.
- **Postgres + pgvector** for embeddings, metrics, and runs.
- **GPU aware**: uses CUDA-enabled PyTorch if available; falls back to CPU.
- **Windows-friendly**: uv-based workflows for PowerShell.

## Quickstart (Windows)

### 1) Prereqs
- Python 3.11+
- [uv](https://github.com/astral-sh/uv)
- Docker Desktop

### 2) Setup
```powershell
uv sync --project .
docker compose up -d
```

### 3) Initialize the database
```powershell
docker compose exec db psql -U ${env:POSTGRES_USER} -d ${env:POSTGRES_DB} -f /migrations/001_init.sql
```

### 4) Run a pipeline
```powershell
uv run --project . photo-curator pipeline --roots "D:\Photos" "E:\Dropbox\Camera Uploads" --top-n 100
```

## CLI examples
```powershell
uv run --project . photo-curator ingest --roots "D:\Photos" "E:\Dropbox\Camera Uploads" --extensions jpg png webp
uv run --project . photo-curator score-technical
uv run --project . photo-curator embed --model "ViT-B-32" --weights-path "C:\models\open_clip_vit_b_32.pt" --batch-size 64
uv run --project . photo-curator score-aesthetic
uv run --project . photo-curator dedup
uv run --project . photo-curator select-top --top-n 100 --output ./output --copy true
uv run --project . photo-curator pipeline --top-n 100
```

## Configuration
- Copy `.env.example` to `.env` and update connection details.
- Copy `config.example.toml` to `config.toml` for defaults.
- CLI flags override config; env vars override config defaults.

### CUDA notes
If you have CUDA-enabled PyTorch installed, the embedding step will use the GPU automatically. Otherwise it uses CPU. You can install a CUDA wheel per PyTorch instructions, then run embeddings with `--device cuda`.

### CLIP weights (offline only)
To avoid any runtime downloads, the embedding step requires a local weights file. Provide `--weights-path` or set `PHOTO_CURATOR_CLIP_WEIGHTS_PATH` in `.env`.

## Project structure
```
.
├── migrations/
├── src/photo_curator/
└── docker-compose.yml
```

## Outputs
- `reports/report.csv`
- `reports/gallery.html`
- Optional output directory with copies (`--copy true`) or symlinks (`--link true`, may require admin privileges on Windows)

## Logs
Structured logs are written to `./logs/` by default.
