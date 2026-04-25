# Branch Intent: 2026-04-22-ingest-consistency-and-db-lifecycle

## Quick Summary
- Branch: `2026-04-22-ingest-consistency-and-db-lifecycle`
- Purpose: Address high-signal pipeline hygiene issues: duplicate file discovery logic, missing DB pool lifecycle cleanup, and LM Studio timeout CLI override.
- Scan first: Use this branch when you are working on the same feature area or error pattern.



## Intent
- Address high-signal pipeline hygiene issues: duplicate file discovery logic, missing DB pool lifecycle cleanup, and LM Studio timeout CLI override.

## Scope
- In scope:
  - Reuse one file-iteration path between legacy `ingest.py` and `pipeline_v1.py`.
  - Ensure DB pools are closed after CLI command execution.
  - Allow LM Studio timeout override via CLI.
  - Apply a small selection-loop efficiency cleanup in `select_top.py`.
  - Remove hardcoded DB credentials from code defaults.
- Out of scope:
  - Full migration from legacy `photos` tables to `files` tables across all modules.
  - Schema redesign or data migrations.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-single-photo-ingest-root-env.md`
  - `docs/branch-intents/2026-04-22-foundation-stack.md`
- Relevant lessons pulled forward:
  - Keep changes incremental and avoid large cross-service refactors in one branch.
  - Pair runtime behavior changes with explicit validation commands.
- Rabbit holes to avoid this time:
  - Do not attempt a full table-contract unification (`photos` vs `files`) in this patch.

## Architecture decisions
- Decision:
  - Keep `pipeline_v1` as active workflow and have legacy ingest iteration reuse its file traversal helper.
- Why:
  - Eliminates immediate duplicated scan logic without destabilizing old `photos`-based paths.
- Tradeoff:
  - `ingest.py` now imports a private helper from `pipeline_v1`; acceptable short-term coupling until legacy ingest is removed or refactored.

## Error log (mandatory)
- Exact error message(s):
  - None encountered during this branch.
- Where seen (command/log/file):
  - N/A.
- Frequency or reproducibility notes:
  - N/A.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Added deterministic DB close behavior to CLI commands via `finally` blocks and `Database.close()` path.
  - Why this was tried:
    - User reported pool cleanup path existed but was never called.
  - Result:
    - Successful; each CLI command now closes the pool before exit.
- Attempt 2:
  - Change made:
    - Added `--lmstudio-timeout-seconds` to `describe` and `pipeline` commands.
  - Why this was tried:
    - User reported timeout was not CLI-configurable.
  - Result:
    - Successful; timeout can now be overridden per run.
- Attempt 3:
  - Change made:
    - Reused `pipeline_v1._iter_files` from `ingest.py`.
  - Why this was tried:
    - User flagged duplicate file discovery logic.
  - Result:
    - Successful; duplicate traversal implementation removed.

## What went right (mandatory)
- Small, scoped changes resolved multiple operational concerns without changing table schemas.

## What went wrong (mandatory)
- Table source-of-truth mismatch (`photos` vs `files`) remains partially unresolved and requires a dedicated migration branch.

## Validation (mandatory)
- Commands run:
  - `uv run --project . ruff check src/photo_curator`
  - `ruff format src/photo_curator/cli.py src/photo_curator/config.py src/photo_curator/db.py src/photo_curator/ingest.py src/photo_curator/select_top.py`
  - `ruff check src/photo_curator/cli.py src/photo_curator/config.py src/photo_curator/db.py src/photo_curator/ingest.py src/photo_curator/select_top.py`
  - `ruff format --check src/photo_curator/cli.py src/photo_curator/config.py src/photo_curator/db.py src/photo_curator/ingest.py src/photo_curator/select_top.py`
- Observed results:
  - `uv run` failed to fetch dependencies from PyPI in this environment (`https://pypi.org/simple/psycopg/`).
  - Direct `ruff` checks/formatting passed for touched Python files.

## Follow-up
- Next branch goals:
  - Decide and execute single source-of-truth migration (`files` preferred) for legacy modules (`dedup`, `embeddings`, `technical`, `aesthetics`, `select_top`, `report`).
- What to try next if unresolved:
  - Add compatibility views or dual-write transitional logic, then migrate readers in phases.
