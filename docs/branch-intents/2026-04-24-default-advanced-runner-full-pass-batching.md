# Branch Intent: 2026-04-24-default-advanced-runner-full-pass-batching

## Quick Summary
- Purpose: Make `python-advanced-runner` perform a full advanced-score pass by default in Docker Compose, with clear batching progress and reduced unnecessary external API calls.
- Keywords: default, advanced, runner, full, pass, batching
## Intent
- Make `python-advanced-runner` perform a full advanced-score pass by default in Docker Compose, with clear batching progress and reduced unnecessary external API calls.

## Scope
- In scope:
  - Update Compose command for `python-advanced-runner` to run full-pass rescoring defaults.
  - Add batch/total progress logging for NIMA advanced scoring.
  - Update README runbook/docs for the new default behavior and tuning.
- Out of scope:
  - Database schema/migration changes.
  - Description algorithm changes.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-24-full-pass-deferred-advanced-rescore.md`
  - `docs/branch-intents/2026-04-23-double-check-advanced-stage.md`
  - `docs/branch-intents/2026-04-22-two-stage-ingest-advanced-nima.md`
- Relevant lessons pulled forward:
  - Keep advanced-stage changes additive and localized.
  - Keep rerun workflow explicit and operationally visible in logs.
- Rabbit holes to avoid this time:
  - No broad pipeline refactor.
  - No changes to unrelated services/routes.

## Architecture decisions
- Decision:
  - Set Compose `python-advanced-runner` default command to `advanced-runner --force-rescore-all --defer-apply-until-complete --skip-descriptions`, with env-tunable batch size.
  - Add candidate-count pre-query and per-batch progress logging in `score_nima`.
- Why:
  - User requested full-pass iteration over a large file set (~20k), explicit batch progress visibility, and avoiding unnecessary API calls during this pass.
- Tradeoff:
  - `--skip-descriptions` defaults the advanced Compose run to scoring-only; description refresh requires explicit command.

## Error log (mandatory)
- Exact error message(s):
  - No runtime exception; requirement/workflow gap from user request.
- Where seen (command/log/file):
  - User request in task conversation.
- Frequency or reproducibility notes:
  - Previous default Compose advanced run did not force full pass and could invoke descriptions depending on provider settings.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Added NIMA candidate counting and batch progress logs before/throughout scoring loop.
  - Why this was tried:
    - Provide visibility for long full-pass runs and batch-oriented progress.
  - Result:
    - Progress logs now include total candidates, estimated batch count, and per-batch boundaries.
- Attempt 2:
  - Change made:
    - Updated Compose advanced-runner command to full-pass/deferred/skip-descriptions defaults and documented behavior in README.
  - Why this was tried:
    - Ensure next `docker compose run --rm python-advanced-runner` naturally follows the desired full-pass overwrite workflow while cutting unneeded external API traffic.
  - Result:
    - Compose defaults align with requested behavior; docs updated with env batch tuning.

## What went right (mandatory)
- Achieved user-requested full-pass overwrite defaults with batching controls.
- Added operational logging for large runs without schema changes.

## What went wrong (mandatory)
- Counting query adds one extra DB read at stage start (expected overhead).

## Validation (mandatory)
- Commands run:
  - `uv run --project . ruff check src/photo_curator/pipeline_v1/advanced_stage.py src/photo_curator/cli.py`
- Observed results:
  - Lint checks pass for touched Python files.

## Follow-up
- Next branch goals:
  - Consider chunked deferred apply execution if write throughput/memory pressure appears on very large libraries.
- What to try next if unresolved:
  - Move pending updates into a temp table + single upsert statement per chunk.
