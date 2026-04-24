# Branch Intent: 2026-04-24-fix-ingest-date-fallback-and-directory-inference

## Intent
- Stop assigning today's date when image taken date cannot be derived.
- Infer taken dates from source directory patterns (including year-month paths like `2009/2009-12/...`) when EXIF is missing.

## Scope
- In scope:
  - Update taken-date resolution fallback behavior in discovery helpers.
  - Expand date inference to include `YYYY-MM` and `YYYY` candidates from filename/path segments.
  - Update base Postgres schema SQL so `photo_taken_at_source` can be `NULL`.
  - Add tests for EXIF precedence, directory month inference, and null fallback.
- Out of scope:
  - Backfilling already-ingested rows in user databases.
  - Changes to unrelated scoring/description stages.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-ingest-consistency-and-db-lifecycle.md`
  - `docs/branch-intents/2026-04-22-improve-ingest-upsert-dedup-cap.md`
- Relevant lessons pulled forward:
  - Keep ingest fixes localized to discovery/common logic and avoid broad pipeline refactors.
  - Preserve upsert flow while changing only metadata derivation behavior.
- Rabbit holes to avoid this time:
  - No schema migration framework work in this patch.
  - No UI/API behavior changes beyond persisted metadata values.

## Architecture decisions
- Decision:
  - Make `_resolve_taken_at` return `(None, None)` when no date hints are available.
  - Add month/year inference heuristics from path and filename before returning null.
  - Remove `NOT NULL DEFAULT 'ingest_time'` from stock/bootstrap schema for `photo_taken_at_source`.
- Why:
  - User-facing correctness: unknown dates should stay unknown, not become ingest-time.
  - Real-world libraries often encode date at month precision in folders.
- Tradeoff:
  - Inferred month/year values use day `1` as placeholder precision anchor.

## Error log (mandatory)
- Exact error message(s):
  - No runtime exception; user-reported behavior bug: files with unknown date are loaded with today's date.
- Where seen (command/log/file):
  - User report referencing source path `/photos/library/2009/2009-12/l_84890506657140a4bc71b2cbab362ed5.jpg` and expected `12/2009` inference.
- Frequency or reproducibility notes:
  - Deterministic for files lacking EXIF and parseable full date under previous fallback logic.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Reviewed `pipeline_v1/common.py` and confirmed `_resolve_taken_at` fallback returns `datetime.now(...), "ingest_time"`.
  - Why this was tried:
    - Verify exact source of today's-date behavior.
  - Result:
    - Confirmed fallback path is root cause.
- Attempt 2:
  - Change made:
    - Implemented month/year inference helpers and null fallback; added targeted unit tests.
  - Why this was tried:
    - Align behavior with user request while keeping ingestion path stable.
  - Result:
    - Logic compiled and linted; initial pytest run failed at collection because `photo_curator` was not on module path.
- Attempt 3:
  - Change made:
    - Re-ran tests with `PYTHONPATH=src` in command invocation.
  - Why this was tried:
    - Match repository test invocation pattern in this environment.
  - Result:
    - Tests validate EXIF precedence, month-directory inference, and null fallback.
- Attempt 4:
  - Change made:
    - Tightened date regexes to parse separator-delimited tokens (`YYYY-MM-DD` / `YYYY-MM`) even when embedded in descriptive directory names, and switched directory scanning order to nearest-parent-first.
    - Added tests for directory names that include text prefixes/suffixes and for rejecting compact digit-only segments (e.g. `20140703`) as accidental date matches.
  - Why this was tried:
    - Follow-up user feedback indicated directory names may contain date tokens plus descriptive text and requested robust parent-directory extraction.
  - Result:
    - Date extraction now supports text-wrapped directory tokens and avoids some false-positive numeric matches.

## What went right (mandatory)
- Date inference improved without touching ingestion SQL write structure.
- New unit tests cover the reported directory layout and regression-protect fallback behavior.

## What went wrong (mandatory)
- Existing deployments may still have old schema defaults until reinitialized or migrated manually.

## Validation (mandatory)
- Commands run:
  - `uv run --project . pytest tests/test_taken_at_resolution.py tests/test_ingest_selection.py`
  - `PYTHONPATH=src uv run --project . pytest tests/test_taken_at_resolution.py tests/test_ingest_selection.py`
  - `uv run --project . ruff check src/photo_curator/pipeline_v1/common.py tests/test_taken_at_resolution.py`
  - `uv run --project . ruff format src/photo_curator/pipeline_v1/common.py tests/test_taken_at_resolution.py`
- Observed results:
  - First pytest command failed during collection (`ModuleNotFoundError: No module named 'photo_curator'`).
  - PYTHONPATH-prefixed pytest command passed.
  - Ruff format/check passed.

## Follow-up
- Next branch goals:
  - Add explicit precision metadata (`day/month/year`) if downstream consumers need finer date-confidence handling.
- What to try next if unresolved:
  - Add opt-in backfill command to recompute `photo_taken_at` from path/EXIF for previously ingested records.
