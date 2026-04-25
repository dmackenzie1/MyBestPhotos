# Branch Intent: 2026-04-23-fix-nima-weights-path-exists-error

## Quick Summary
- Purpose: Fix advanced runner failure occurring during NIMA model weight path checks/download so `photo-curator advanced-runner` can continue instead of crashing at `_ensure_weights`.
- Keywords: fix, nima, weights, path, exists, error
## Intent
- Fix advanced runner failure occurring during NIMA model weight path checks/download so `photo-curator advanced-runner` can continue instead of crashing at `_ensure_weights`.

## Scope
- In scope:
  - Harden NIMA weight path handling around `Path.exists()` and cache-directory creation.
  - Keep model/scoring behavior unchanged when paths are healthy.
  - Add resilient fallback pathing to a temp cache directory.
- Out of scope:
  - Changing scoring math, model architecture, or CLI contracts.
  - Reworking Docker compose service topology.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-two-stage-ingest-advanced-nima.md`
  - `docs/branch-intents/2026-04-22-compose-second-pass-advanced-runner-container.md`
  - `docs/branch-intents/2026-04-22-python-runner-startup-gpu-cache.md`
- Relevant lessons pulled forward:
  - Keep runner fixes minimal, explicit, and operationally focused.
  - Preserve additive behavior and avoid broad architectural rewrites.
- Rabbit holes to avoid this time:
  - No migration/schema changes.
  - No dependency or infra redesign.

## Architecture decisions
- Decision:
  - Add OSError-safe weight path checks and fallback to `${TMPDIR:-/tmp}/photo-curator-cache/nima/pretrained_weights.pth` when primary cache path cannot be accessed/created.
- Why:
  - The crash occurs before scoring on filesystem operations; fallback path allows inference startup in constrained mounts/permissions scenarios.
- Tradeoff:
  - Weights may live in temp storage for affected runs, requiring re-download on ephemeral hosts.

## Error log (mandatory)
- Exact error message(s):
  - Traceback points at `src/photo_curator/nima/inference.py`, `_ensure_weights`, line containing `if weights_path.exists():` during `photo-curator advanced-runner`.
- Where seen (command/log/file):
  - `mybestphotos-python-advanced-runner` container logs from the user.
- Frequency or reproducibility notes:
  - Reproduced in reported stack; exact exception tail was truncated in the provided snippet.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Wrapped `_ensure_weights` existence checks in `try/except OSError` with warning logs.
  - Why this was tried:
    - Prevent crash if the cache path cannot be stat'ed.
  - Result:
    - Successful code update.
- Attempt 2:
  - Change made:
    - Added fallback cache path check under tmp dir and return existing fallback file when present.
  - Why this was tried:
    - Reuse previously downloaded weights even when primary path is inaccessible.
  - Result:
    - Successful code update.
- Attempt 3:
  - Change made:
    - Wrapped cache directory creation in `_download_weights` with OSError handling and fallback dir creation in tmp.
  - Why this was tried:
    - Avoid failing before download due mkdir permissions/mount errors.
  - Result:
    - Successful code update.

## What went right (mandatory)
- Fix stayed localized to NIMA inference path handling with no API/CLI changes.
- Existing success path still returns primary cache file when available.

## What went wrong (mandatory)
- User-provided log lacked final exception line, so the exact OS error type/message could not be directly asserted.

## Validation (mandatory)
- Commands run:
  - `uv run --project . ruff format src/photo_curator/nima/inference.py`
  - `uv run --project . ruff check src/photo_curator/nima/inference.py`
  - `PYTHONPATH=src uv run --project . python -m unittest tests/test_nima_scoring.py`
- Observed results:
  - Formatting/lint command(s) completed successfully.
  - Targeted NIMA scoring unit tests passed.

## Follow-up
- Next branch goals:
  - Add a focused unit test that simulates `Path.exists()`/mkdir OSError in inference path handling.
- What to try next if unresolved:
  - Log and verify effective runtime value of `PHOTO_CURATOR_CACHE_DIR` inside the container, plus mount permissions on `/data/cache`.
