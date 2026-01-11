# AI Contribution Guide

This repository has no nested AGENTS yet; this file applies to all paths unless a deeper AGENTS.md is added. Pair it with `coding_rules.txt` at the root.

## Core expectations
- Favor incremental, low-drama patches that match existing patterns in each service; reuse helpers in `services/common` instead of re-inventing payload/data classes.
- Python services run under `uv` with Python 3.11+ (most hosts now use 3.12.3); prefer `uv run --project ...` for commands and keep Docker Compose dev paths intact. When touching Python, keep compatibility with 3.11 and 3.12.
- Prefer `ruff format` + `ruff check` for Python style (pinned to the latest release in both `pyproject.toml` and pre-commit); do not introduce alternate formatters/linters without justification.
- Keep Docker Compose names/ports stable; when changing stack wiring, update compose files and service READMEs together.
- Enforce LF line endings (no CRLF) to keep Docker containers happy and avoid noisy diffs; VS Code settings already default to `\n`.
- Whisper/WhisperX and ffmpeg handling should be explicit—log device/codec choices and keep CUDA toggles (`WHISPER_DEVICE`, `WHISPERX_COMPUTE_TYPE`) configurable.
- Secrets live in env vars or `api_key.txt`; never bake them into code or sample configs.

## Service-specific habits
- **Capture/Transcribe:** stick to the existing CLI/env surface; any new flags should map cleanly to env vars and be documented in the service README.
- **Web (FastAPI):** keep routes under `/api/v1`, return JSON-friendly types, and use existing serialization helpers in `app/utterance_utils.py` and `app/job_messages.py`.
- **Web UI (Vue 3 + Vite):** emitted assets live in `services/web/static`; keep the dark theme and status-first layout intact when adding UI affordances.

## Testing and validation
- Default command: `uv run pre-commit run --all-files` plus targeted service checks as needed (pytest for web, npm/vite checks for UI when the change touches frontend files).
- Avoid long-lived background services in tests; prefer in-memory stubs (see `InMemoryJobQueue`) and short-lived fixtures.

## Versioning expectations
- Keep version numbers in sync across artifacts when they exist, but only bump them for substantive work (major refactors or 100+ lines of change). Minor touch-ups can ship without version increments; document the rationale in the changelog when bumps are required.

## Documentation and PR etiquette
- Update READMEs/roadmaps when behavior changes. Keep changelog entries concise and date-stamped.
- Summaries should call out API/CLI deltas and any deploy-impacting changes (migrations, new env vars, or new compose services).
- When adding new configs (VS Code, pre-commit, scripts), explain how they interplay with `uv` and Docker.

## File-scope note
Files under `services/web/` have additional guidance in `services/web/AGENTS.md`.
