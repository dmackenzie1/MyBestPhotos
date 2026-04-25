# Branch Intent: 2026-04-24-full-pass-deferred-advanced-rescore

## Quick Summary
- Branch: `2026-04-24-full-pass-deferred-advanced-rescore`
- Purpose: Let users rerun advanced scoring for every image while keeping currently visible scores untouched until the full scoring pass is done.
- Scan first: Use this branch when you are working on the same feature area or error pattern.



## Intent
- Let users rerun advanced scoring for every image while keeping currently visible scores untouched until the full scoring pass is done.

## Scope
- In scope:
  - Add CLI flags for full-pass advanced rescoring.
  - Add deferred-write mode so score updates can be applied after compute completes.
  - Document new rerun workflow in README.
- Out of scope:
  - Schema migrations.
  - Description stage algorithm changes.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-two-stage-ingest-advanced-nima.md`
  - `docs/branch-intents/2026-04-23-double-check-advanced-stage.md`
  - `docs/branch-intents/2026-04-23-score-improvements-from-real-data.md`
- Relevant lessons pulled forward:
  - Keep advanced-stage fixes localized and additive.
  - Preserve rerunnable behavior and avoid broad redesigns.
- Rabbit holes to avoid this time:
  - No DB schema changes or unrelated pipeline refactors.

## Architecture decisions
- Decision:
  - Add `--force-rescore-all` and `--defer-apply-until-complete` flags on `score-nima` and `advanced-runner`.
  - Implement deferred apply in `score_nima` by collecting computed updates and writing them after selection/scoring loop finishes.
- Why:
  - User needs a full pass through all images without row-by-row overwrite visibility.
- Tradeoff:
  - Deferred mode holds update payloads in memory until apply phase and writes happen at the end.

## Error log (mandatory)
- Exact error message(s):
  - No runtime exception; this is a workflow/behavior gap requested by user.
- Where seen (command/log/file):
  - User report about wanting full reruns without immediately replacing existing scores.
- Frequency or reproducibility notes:
  - Current behavior is deterministic: scores update incrementally during rerun.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Reviewed `score_nima` selection/write behavior and identified that immediate upserts are done per image.
  - Why this was tried:
    - Confirm where to hook a deferred write mode.
  - Result:
    - Confirmed `score_nima` is the right single place for minimal change.
- Attempt 2:
  - Change made:
    - Added force-full-pass + deferred-apply controls to advanced stage and CLI wiring.
  - Why this was tried:
    - Provide explicit user-selectable rerun mode with minimal API/contract churn.
  - Result:
    - Local implementation complete; lint checks pass.

## What went right (mandatory)
- Changes are constrained to advanced-stage scoring and CLI options.
- New workflow is explicit and opt-in.

## What went wrong (mandatory)
- Deferred apply currently performs row-wise upserts at apply time; no bulk SQL path yet.

## Validation (mandatory)
- Commands run:
  - `uv run --project . ruff check src/photo_curator/pipeline_v1/advanced_stage.py src/photo_curator/cli.py`
- Observed results:
  - Formatting/check pass for touched Python files.

## Follow-up
- Next branch goals:
  - Add optional transactional/bulk apply path if write throughput becomes a bottleneck.
- What to try next if unresolved:
  - If memory usage grows too much on very large libraries, switch deferred payload storage to a temp table.
