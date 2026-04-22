# Branch Intent: 2026-04-22-improve-ingest-upsert-dedup-cap

## Intent
- Make ingest safer for iterative local runs by sampling a manageable file subset each run and preventing unlimited duplicate file records while still allowing updates to existing paths.

## Scope
- In scope:
  - Default discovery selection to a random 200-file batch for each run.
  - Keep upsert behavior for existing `(source_root, relative_path)` rows.
  - Skip *new* inserts when duplicate filename or sha256 count has already reached a configurable cap.
  - Add targeted tests for duplicate-cap decision logic.
  - Update README env documentation for new ingest defaults.
- Out of scope:
  - Schema migrations or adding new unique indexes.
  - Rewriting discover/insert flow into bulk SQL operations.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-ingest-consistency-and-db-lifecycle.md`
  - `docs/branch-intents/2026-04-22-planning-ingest-browse-cleanups.md`
- Relevant lessons pulled forward:
  - Keep changes incremental and avoid broad schema refactors.
  - Keep behavior changes explicit in docs and covered by focused tests.
- Rabbit holes to avoid this time:
  - Do not attempt full legacy table contract migration in this branch.

## Architecture decisions
- Decision:
  - Enforce duplicate guard in Python discover flow using pre-insert counts and a helper predicate.
- Why:
  - Allows immediate behavior change without needing complex SQL triggers/check constraints for “max two duplicates”.
- Tradeoff:
  - Adds two small count queries per discovered candidate; acceptable for capped/batch ingest and local dev workflows.

## Error log (mandatory)
- Exact error message(s):
  - None encountered while implementing this branch.
- Where seen (command/log/file):
  - N/A
- Frequency or reproducibility notes:
  - N/A

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Updated settings defaults to `ingest_limit=200`, `ingest_selection_strategy=random`, and added `duplicate_cap_per_filename_or_sha`.
  - Why this was tried:
    - Align default behavior with user request for random 200-at-a-time processing and capped duplicates.
  - Result:
    - Successful.
- Attempt 2:
  - Change made:
    - Added duplicate-cap skip helper and wired discover insert flow to skip only new rows that exceed cap while permitting updates to existing path records.
  - Why this was tried:
    - Keep iterative reruns idempotent and avoid duplicate blow-up in a persistent DB.
  - Result:
    - Successful.

## What went right (mandatory)
- Changes stayed localized to config/discover logic and simple tests; no schema or API contract churn.

## What went wrong (mandatory)
- Duplicate cap enforcement currently uses pre-insert query counts and is not atomic under high concurrency.

## Validation (mandatory)
- Commands run:
  - `uv run --project . ruff format src/photo_curator/config.py src/photo_curator/pipeline_v1.py tests/test_ingest_selection.py`
  - `ruff format src/photo_curator/config.py src/photo_curator/pipeline_v1.py tests/test_ingest_selection.py`
  - `ruff check src/photo_curator/config.py src/photo_curator/pipeline_v1.py tests/test_ingest_selection.py`
  - `PYTHONPATH=src python -m unittest tests/test_ingest_selection.py`
- Observed results:
  - `uv run` failed in this environment due to external dependency download tunnel failure for Pillow.
  - Direct `ruff` formatting/check and targeted unittest suite passed.

## Follow-up
- Next branch goals:
  - If needed, move duplicate-cap guard into a SQL-side strategy (materialized counters/trigger) for stronger concurrency guarantees.
- What to try next if unresolved:
  - Add transaction-level locking around count+insert path for strict race-free caps.
