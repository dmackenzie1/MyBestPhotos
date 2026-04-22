# Branch Intent: 2026-04-22-fix-exif-pipeline-pool-indexes

## Intent
- Address the review findings around EXIF JSON bloat, oversized `pipeline_v1.py`, DB pool error handling, redundant NIMA metric recomputation, brittle category extraction, and missing label indexes.

## Scope
- In scope:
  - Encode binary EXIF values into JSON-safe hex objects before writing JSONB.
  - Split pipeline v1 logic into focused stage modules with a compatibility export layer.
  - Add `pg.Pool` error handler in app server DB module.
  - Make NIMA scoring reuse `file_metrics` values when present and recompute only when missing.
  - Replace naive category substring checks with regex/token-boundary matching.
  - Add indexes for frequently queried label flags.
- Out of scope:
  - Full ML/semantic category model integration.
  - Changing NIMA ownership between runner commands.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-validate-external-code-review.md`
  - `docs/branch-intents/2026-04-22-fix-review-actionable-items.md`
  - `docs/branch-intents/2026-04-22-two-stage-ingest-advanced-nima.md`
- Relevant lessons pulled forward:
  - Keep fixes incremental and directly verifiable.
  - Preserve current two-stage behavior while tightening implementation details.
- Rabbit holes to avoid this time:
  - Broad schema redesign beyond targeted indexes.

## Architecture decisions
- Decision:
  - Convert `pipeline_v1.py` into a package (`pipeline_v1/`) with stage-specific modules and lazy-import facade for backward compatibility.
- Why:
  - Reduces single-file complexity without forcing immediate importer rewrites.
- Tradeoff:
  - Additional module boundaries increase indirection but improve maintainability.

## Error log (mandatory)
- Exact error message(s):
  - `F841 Local variable lmstudio_used is assigned to but never used`
  - `ModuleNotFoundError: No module named 'cv2'` (during unit-test module import path)
- Where seen (command/log/file):
  - `uv run --project . ruff check ...`
  - `PYTHONPATH=src python -m unittest ...`
- Frequency or reproducibility notes:
  - Reproducible before fixes; resolved by removing unused variable and using lazy imports in `pipeline_v1.__init__`.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Split pipeline into discovery/metrics/description/advanced/common modules and added compatibility exports.
  - Why this was tried:
    - Directly addresses single-file orchestration complexity.
  - Result:
    - Successful after lazy import adjustments.
- Attempt 2:
  - Change made:
    - Updated NIMA stage query to fetch existing metrics and reuse them unless missing.
  - Why this was tried:
    - Remove duplicate metric computation overhead.
  - Result:
    - Successful.
- Attempt 3:
  - Change made:
    - Added EXIF bytes encoding and DB/SQL index hardening updates.
  - Why this was tried:
    - Fix JSONB bloat and common query performance hotspot.
  - Result:
    - Successful.

## What went right (mandatory)
- All requested issues were addressed with localized edits and no CLI contract break.

## What went wrong (mandatory)
- Initial package export approach eagerly imported OpenCV-dependent modules, breaking tests in environments without `cv2`.

## Validation (mandatory)
- Commands run:
  - `uv run --project . ruff format src/photo_curator/pipeline_v1 src/photo_curator/cli.py src/photo_curator/ingest.py tests/test_ingest_selection.py tests/test_nima_scoring.py`
  - `uv run --project . ruff check src/photo_curator/pipeline_v1 src/photo_curator/cli.py src/photo_curator/ingest.py tests/test_ingest_selection.py tests/test_nima_scoring.py`
  - `PYTHONPATH=src python -m unittest tests/test_ingest_selection.py tests/test_nima_scoring.py`
  - `npm run -w services/app/server build`
- Observed results:
  - Ruff format/check passed after fixes.
  - Targeted unit tests passed.
  - Server TypeScript build passed.

## Follow-up
- Next branch goals:
  - Add DB migration/backfill utility for historical EXIF JSON rows if required.
- What to try next if unresolved:
  - If category extraction quality is still weak, promote to embedding/ML-based categorization in advanced runner stage.
