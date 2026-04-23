# Branch Intent: 2026-04-23-clip-aesthetic-scoring-primary-schema

## Intent
- Replace broken NIMA/heuristic aesthetic behavior with working CLIP-based scoring that auto-downloads weights and produces meaningful spread for ranking.

## Scope
- In scope:
  - Update CLIP aesthetics loading to auto-download pretrained weights on first use.
  - Add CLIP aesthetic scoring over `files`/`file_metrics` rows with batched image encoding and DB upserts.
  - Wire advanced runner scoring path to use CLIP score instead of heuristic/NIMA fallback source.
  - Add CLI command to rescore missing aesthetic values and log score distribution.
- Out of scope:
  - Schema migrations/new tables.
  - Full redesign of downstream ranking math.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-23-fix-nima-weights-path-exists-error.md`
  - `docs/branch-intents/2026-04-22-two-stage-ingest-advanced-nima.md`
- Relevant lessons pulled forward:
  - Keep runner changes localized and additive.
  - Prefer resilient model-loading behavior over brittle filesystem assumptions.
- Rabbit holes to avoid this time:
  - Avoid broad pipeline rewrites or schema churn.

## Architecture decisions
- Decision:
  - Use `open_clip.create_model_and_transforms(model_name)` for aesthetics inference and text prompt scoring with cosine-difference + sigmoid.
- Why:
  - Matches known-good embeddings loading behavior and removes manual weight path dependency.
- Tradeoff:
  - First run incurs model download latency.

## Error log (mandatory)
- Exact error message(s):
  - Known issue described by user: NIMA/heuristic fallback path yields nearly identical scores and does not discriminate aesthetics.
- Where seen (command/log/file):
  - `src/photo_curator/pipeline_v1/advanced_stage.py` around `score_nima` logic.
- Frequency or reproducibility notes:
  - Reproducible when NIMA weights are unavailable or fallback path is active.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Reworked `src/photo_curator/aesthetics.py` to load CLIP with auto-download, add reusable CLIP scorer, and implement batched scoring/upserts for `files` + `file_metrics`.
  - Why this was tried:
    - Centralize CLIP aesthetic math and reuse it across CLI + advanced stage.
  - Result:
    - Successful; lint/compile checks passed.
- Attempt 2:
  - Change made:
    - Updated `advanced_stage.score_nima` to compute `nima_mean` from CLIP score per image and keep downstream blending logic unchanged.
  - Why this was tried:
    - Replace fragile heuristic/NIMA dependency while preserving existing composition/keep-score behavior.
  - Result:
    - Successful; no API break in command flow.
- Attempt 3:
  - Change made:
    - Added `score-aesthetic` CLI command and threaded configured `clip_model`/device settings through advanced runner and score-nima command paths.
  - Why this was tried:
    - Enable backfilling missing aesthetics and ensure config-driven model/device selection.
  - Result:
    - Successful; lint/compile checks passed.

## What went right (mandatory)
- CLIP scoring now follows a single reusable code path and no longer requires manual local weight files.
- Existing downstream score-shaping formulas remain intact.

## What went wrong (mandatory)
- No integration DB run was executed in this environment, so validation is limited to static checks/compile.

## Validation (mandatory)
- Commands run:
  - `uv run --project . ruff format src/photo_curator/aesthetics.py src/photo_curator/pipeline_v1/advanced_stage.py src/photo_curator/pipeline_v1/__init__.py src/photo_curator/cli.py`
  - `uv run --project . ruff check src/photo_curator/aesthetics.py src/photo_curator/pipeline_v1/advanced_stage.py src/photo_curator/pipeline_v1/__init__.py src/photo_curator/cli.py`
  - `uv run --project . python -m compileall src/photo_curator`
- Observed results:
  - Format/check passed.
  - Compileall passed.

## Follow-up
- Next branch goals:
  - Add unit tests for CLIP prompt differential scoring and advanced-stage CLIP fallback behavior.
- What to try next if unresolved:
  - If score spread remains low on real datasets, tune prompt set and optionally apply temperature scaling before sigmoid.
