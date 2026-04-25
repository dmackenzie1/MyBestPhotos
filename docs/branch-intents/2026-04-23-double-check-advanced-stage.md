# Branch Intent: 2026-04-23-double-check-advanced-stage

## Quick Summary
- Purpose: Double-check `src/photo_curator/pipeline_v1/advanced_stage.py` and correct any regressions in the advanced scoring path.
- Keywords: double, check, advanced, stage
## Intent
- Double-check `src/photo_curator/pipeline_v1/advanced_stage.py` and correct any regressions in the advanced scoring path.

## Scope
- In scope:
  - Review recent branch-intent history for CLIP/NIMA changes.
  - Audit `advanced_stage.py` for logic mismatches.
  - Apply a minimal fix and run targeted validation.
- Out of scope:
  - Broad pipeline redesign or schema changes.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-23-clip-aesthetic-scoring-primary-schema.md`
  - `docs/branch-intents/2026-04-23-clip-aesthetic-followup-validation.md`
- Relevant lessons pulled forward:
  - Keep fixes localized and verify runtime behavior, not just lint.
  - Avoid silent quality regressions in scoring paths.
- Rabbit holes to avoid this time:
  - No unrelated refactors across other pipeline stages.

## Architecture decisions
- Decision:
  - Use the already-loaded CLIP scorer in `score_nima` to derive the primary `nima_mean` value, while preserving downstream blending math and DB writes.
- Why:
  - Current code instantiated CLIP scorer but never used it, then still called NIMA inference.
- Tradeoff:
  - Requires converting each loaded OpenCV image to PIL before scoring.

## Error log (mandatory)
- Exact error message(s):
  - No runtime exception observed; this was a logic/regression audit.
- Where seen (command/log/file):
  - `src/photo_curator/pipeline_v1/advanced_stage.py` static review.
- Frequency or reproducibility notes:
  - Deterministic in code: CLIP scorer object unused on every run.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Audited `advanced_stage.py` and identified unused imports/variables (`heuristic_score`, `assess_quality` path still active, `clip_scorer` unused).
  - Why this was tried:
    - Confirm whether the branch is actually using CLIP after recent migration.
  - Result:
    - Found clear mismatch: code does not use CLIP for the primary score.
- Attempt 2:
  - Change made:
    - Replaced per-image `assess_quality(image)` call with CLIP scorer invocation and removed stale NIMA imports.
  - Why this was tried:
    - Align runtime with intended CLIP-based aesthetic scoring behavior.
  - Result:
    - Successful local patch; targeted lint/unit checks pass.

## What went right (mandatory)
- Found and fixed a concrete regression with a minimal edit footprint.
- Preserved existing downstream score shaping and persistence logic.

## What went wrong (mandatory)
- No end-to-end DB/inference integration run was performed in this environment.

## Validation (mandatory)
- Commands run:
  - `uv run --project . ruff check src/photo_curator/pipeline_v1/advanced_stage.py`
  - `PYTHONPATH=src uv run --project . python -m unittest tests/test_nima_scoring.py`
- Observed results:
  - Lint passes.
  - Targeted NIMA-related tests pass.

## Follow-up
- Next branch goals:
  - Add/expand tests that assert CLIP scorer usage path in `advanced_stage.score_nima`.
- What to try next if unresolved:
  - Run integration scoring on a small fixture dataset and compare distribution logs before/after.
