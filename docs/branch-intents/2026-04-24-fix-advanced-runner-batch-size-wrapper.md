# Branch Intent: 2026-04-24-fix-advanced-runner-batch-size-wrapper

## Intent
- Fix `advanced-runner` CLI failure where `run_advanced_runners()` rejects `batch_size` and related advanced-scoring kwargs.

## Scope
- In scope:
  - Align `pipeline_v1.__init__.py` wrapper signature with `advanced_stage.run_advanced_runners`.
  - Confirm lint passes for touched files.
- Out of scope:
  - Advanced scoring algorithm behavior.
  - Docker Compose command defaults.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-24-default-advanced-runner-full-pass-batching.md`
  - `docs/branch-intents/2026-04-24-full-pass-deferred-advanced-rescore.md`
  - `docs/branch-intents/2026-04-23-double-check-advanced-stage.md`
- Relevant lessons pulled forward:
  - Keep advanced-stage fixes additive and localized.
  - Avoid broad refactors while addressing runner regressions.
- Rabbit holes to avoid this time:
  - No schema/migration work.
  - No changes to model scoring math.

## Architecture decisions
- Decision:
  - Extend the public `pipeline_v1.run_advanced_runners` wrapper to accept and forward `batch_size`, `force_rescore_all`, and `defer_apply_until_complete`.
- Why:
  - The CLI imports the wrapper, not the stage module directly; missing kwargs there trigger runtime `TypeError`.
- Tradeoff:
  - Slightly wider wrapper surface area, but now correctly mirrors stage API and CLI usage.

## Error log (mandatory)
- Exact error message(s):
  - `TypeError: run_advanced_runners() got an unexpected keyword argument 'batch_size'`
- Where seen (command/log/file):
  - Runtime traceback from `src/photo_curator/cli.py` at `advanced_runner_cmd` call to `run_advanced_runners`.
- Frequency or reproducibility notes:
  - Reproducible whenever `advanced-runner` command passes advanced kwargs through `pipeline_v1.__init__.py` wrapper.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Inspected `src/photo_curator/cli.py`, `src/photo_curator/pipeline_v1/__init__.py`, and `src/photo_curator/pipeline_v1/advanced_stage.py` signatures.
  - Why this was tried:
    - Validate whether mismatch is callsite bug or wrapper export drift.
  - Result:
    - Identified wrapper signature drift (missing kwargs) while stage implementation accepts kwargs.
- Attempt 2:
  - Change made:
    - Updated wrapper function signature + forwarding call in `src/photo_curator/pipeline_v1/__init__.py`.
  - Why this was tried:
    - Restore API parity and unblock CLI advanced runner.
  - Result:
    - Lint/checks pass and keyword forwarding now matches CLI call.

## What went right (mandatory)
- Root cause was isolated quickly to wrapper drift.
- Fix was small and localized to one module export surface.

## What went wrong (mandatory)
- Regression was introduced by adding new kwargs in stage/CLI without updating the top-level wrapper.

## Validation (mandatory)
- Commands run:
  - `uv run --project . ruff check src/photo_curator/pipeline_v1/__init__.py src/photo_curator/cli.py src/photo_curator/pipeline_v1/advanced_stage.py`
- Observed results:
  - Ruff check passed.

## Follow-up
- Next branch goals:
  - Add a lightweight CLI smoke test for `advanced-runner` arg passthrough to catch wrapper drift.
- What to try next if unresolved:
  - If runtime still fails, run `uv run --project . python -m photo_curator.cli advanced-runner --help` and targeted command invocation against test DB to validate entrypoint wiring.
