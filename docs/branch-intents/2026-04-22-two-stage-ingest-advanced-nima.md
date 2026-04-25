# Branch Intent: 2026-04-22-two-stage-ingest-advanced-nima

## Quick Summary
- Purpose: Evolve the runner into a practical two-stage architecture (base ingest + advanced runners) and add a first NIMA-style aesthetic scoring stage without over-engineering.
- Keywords: two, stage, ingest, advanced, nima
## Intent
- Evolve the runner into a practical two-stage architecture (base ingest + advanced runners) and add a first NIMA-style aesthetic scoring stage without over-engineering.

## Scope
- In scope:
  - Clarify two-stage architecture in docs and CLI.
  - Add advanced-runner path with resumable NIMA-style batch scoring.
  - Extend schema for advanced scoring fields in `file_metrics`.
  - Keep existing ingest/metrics/description behavior intact and additive.
- Out of scope:
  - Full ML model serving stack for real NIMA inference.
  - Queue system redesign.
  - Comprehensive stale-policy framework for all future enrichers.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-audit-ingest-browse-search-scoring.md`
  - `docs/branch-intents/2026-04-22-improve-ingest-upsert-dedup-cap.md`
- Relevant lessons pulled forward:
  - Prefer additive, localized changes over broad rewrites.
  - Keep fallback validation paths when `uv run` dependency downloads fail in this environment.
- Rabbit holes to avoid this time:
  - Avoid replacing the entire pipeline with a new framework.
  - Avoid introducing heavyweight model dependencies for the first NIMA step.

## Architecture decisions
- Decision:
  - Keep deterministic file discovery + base metrics as canonical base ingest and add a separate advanced runner layer for rerunnable enrichment.
- Why:
  - Matches requested stable-vs-derived philosophy with minimal disruption.
- Tradeoff:
  - First NIMA implementation is heuristic (`nima_style_v0`) rather than a true trained NIMA model.

## Error log (mandatory)
- Exact error message(s):
  - `Failed to download regex==2026.4.4`
  - `tunnel error: unsuccessful`
- Where seen (command/log/file):
  - During `uv run --project . ruff format ... && uv run --project . ruff check ...`.
- Frequency or reproducibility notes:
  - Reproduced in this session due external network/proxy restrictions on wheel download.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Added `score_nima` batch runner and `run_advanced_runners` orchestration in `pipeline_v1.py`.
  - Why this was tried:
    - Establish a practical advanced-runner pattern that is resumable and safe to rerun.
  - Result:
    - Successful.
- Attempt 2:
  - Change made:
    - Added CLI commands `base-ingest`, `score-nima`, and `advanced-runner`; updated `pipeline` summary to include NIMA output.
  - Why this was tried:
    - Make two-stage operation explicit and operable without a rewrite.
  - Result:
    - Successful.
- Attempt 3:
  - Change made:
    - Extended schema bootstrap/init SQL with `nima_score`, `aesthetic_score`, `keep_score`, and advanced metadata tracking fields.
  - Why this was tried:
    - Persist advanced derived results separately from stable file truth while staying in existing `file_metrics` table.
  - Result:
    - Successful.
- Attempt 4:
  - Change made:
    - Updated architecture/scoring/README docs and added targeted NIMA helper tests.
  - Why this was tried:
    - Ensure the intended direction is clear and validated.
  - Result:
    - Successful.

## What went right (mandatory)
- The change stayed incremental and reused existing pipeline patterns.
- New advanced runner is DB-driven and batch-based, matching current stack simplicity.

## What went wrong (mandatory)
- `uv run` validation remains blocked by dependency download restrictions in this environment, requiring fallback checks.

## Validation (mandatory)
- Commands run:
  - `uv run --project . ruff format src/photo_curator/pipeline_v1.py src/photo_curator/cli.py tests/test_nima_scoring.py && uv run --project . ruff check src/photo_curator/pipeline_v1.py src/photo_curator/cli.py tests/test_nima_scoring.py`
  - `ruff format src/photo_curator/pipeline_v1.py src/photo_curator/cli.py tests/test_nima_scoring.py`
  - `ruff check src/photo_curator/pipeline_v1.py src/photo_curator/cli.py tests/test_nima_scoring.py`
  - `PYTHONPATH=src python -m unittest tests/test_ingest_selection.py tests/test_config_ingest_env_aliases.py tests/test_nima_scoring.py`
- Observed results:
  - `uv run` failed due external wheel download tunnel failure.
  - Ruff format/check passed via local tooling.
  - Targeted unittest suite passed.

## Follow-up
- Next branch goals:
  - Swap `nima_style_v0` for a real model-backed inference path (e.g., ONNX/PyTorch) behind the same runner contract.
  - Add stale-selection policy knobs (e.g., by `advanced_metadata_updated_at` age and model version mismatch).
- What to try next if unresolved:
  - If batch performance slows on large libraries, add indexes and keyset-style selection for advanced runners.
