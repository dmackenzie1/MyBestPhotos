# Branch Intent: 2026-04-25-standard-code-review

## Quick Summary
- Purpose: Perform a standard repo-wide code review pass focused on DB schema, backend/frontend code quality, and obvious dead/unused code.
- Keywords: standard, code, review
## Intent
- Perform a standard repo-wide code review pass focused on DB schema, backend/frontend code quality, and obvious dead/unused code.

## Scope
- In scope:
  - Static inspection of Postgres schema SQL, Python pipeline code, API server code, and React UI code.
  - Run practical lint/build/test commands to surface obvious failures.
  - Document high-signal issues and recommended next fixes.
- Out of scope:
  - Large refactors.
  - Behavioral or API changes.
  - Repairing every issue found in this same branch.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-25-audit-stream-consolidated.md`
  - `docs/branch-intents/2026-04-24-full-code-review-hygiene-pass.md`
  - `docs/branch-intents/2026-04-24-complete-code-review-pass-2.md`
- Relevant lessons pulled forward:
  - Keep review passes focused on high-impact correctness and hygiene issues.
  - Capture exact command output and avoid speculative claims.
- Rabbit holes to avoid this time:
  - Broad architecture rewrites while only reviewing.
  - UI redesign churn not tied to concrete defects.

## Architecture decisions
- Decision:
  - Deliver this task as an audit report plus branch-intent log, without large code rewrites.
- Why:
  - User requested a broad standard review (“go through it”), not a specific feature implementation.
- Tradeoff:
  - Faster signal and lower risk now, but remediation still needed in follow-up branches.

## Error log (mandatory)
- Exact error message(s):
  - `invalid-syntax: Expected an indented block after if statement`
  - `Failed to spawn: pre-commit`
  - `Cannot find module 'react-router-dom' or its corresponding type declarations.`
  - `ModuleNotFoundError: No module named 'photo_curator'`
  - `ModuleNotFoundError: No module named 'pydantic'`
  - `ModuleNotFoundError: No module named 'scripts'`
- Where seen (command/log/file):
  - `uv run ruff check .` -> `src/photo_curator/pipeline_run.py:313`
  - `uv run pre-commit run --all-files`
  - `npm run build`
  - `uv run pytest -q`
  - `PYTHONPATH=src uv run pytest -q`
- Frequency or reproducibility notes:
  - Reproducible on each run in this environment.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Ran standard lint/test/build checks directly from repo root.
  - Why this was tried:
    - Establish objective baseline health across Python + TypeScript + workspace tooling.
  - Result:
    - Found a blocking Python syntax error and multiple environment/dependency/tooling gaps.
- Attempt 2:
  - Change made:
    - Performed targeted static inspection across schema SQL, backend routes/query layer, and UI components to identify dead code and drift risks.
  - Why this was tried:
    - User explicitly asked for schema/UI/dead-code review and “anything glaring.”
  - Result:
    - Confirmed dead/duplicate UI artifacts and build/setup inconsistencies.

## What went right (mandatory)
- High-signal blockers were quickly identified with reproducible commands.
- Review included schema + backend + UI coverage as requested.

## What went wrong (mandatory)
- Environment is missing `pre-commit` binary and Python deps needed for full test pass.
- Node workspace dependency state appears incomplete (missing `react-router-dom` install despite package declaration).

## Validation (mandatory)
- Commands run:
  - `uv run pre-commit run --all-files`
  - `uv run ruff check .`
  - `uv run pytest -q`
  - `PYTHONPATH=src uv run pytest -q`
  - `npm run build`
  - `rg -n "MapPlaceholder" services/app/client/src`
  - `find services/app/client/src -maxdepth 4 -type f | rg '\\.js$|\\.tsbuildinfo$'`
- Observed results:
  - Lint/build/test surfaced concrete failures documented above.
  - Static checks found orphaned `MapPlaceholder` and duplicate transpiled `.js` files in TS source tree.

## Follow-up
- Next branch goals:
  - Fix the syntax error in `pipeline_run.py`.
  - Normalize Python test invocation/deps for clean `pytest` collection.
  - Repair Node workspace install state and remove accidental generated JS artifacts from `services/app/client/src`.
- What to try next if unresolved:
  - Add/verify explicit onboarding commands in README (`uv sync`, workspace install) and enforce generated-file exclusions via gitignore/lint gate.

## Consolidated follow-up (2026-04-25, same review stream)
- User-reported errors revisited:
  - `IndentationError: expected an indented block after 'if' statement on line 312`
  - `ERROR: column "clip_model_version" does not exist`
- Changes applied in this same stream:
  - Fixed indentation in `src/photo_curator/pipeline_run.py` under `if null_counts:`.
  - Updated API health query (`services/app/server/src/index.ts`) to read `clip_model_version` via `to_jsonb(p)->>'clip_model_version'` for backward compatibility.
  - Added `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` backfills for `pipeline_runs` core metadata/count columns in `services/postgres/bootstrap.sql` so older volumes are upgraded at bootstrap time.
- Validation snapshots:
  - `uv run ruff check src/photo_curator/pipeline_run.py` -> pass.
  - `python -m py_compile src/photo_curator/pipeline_run.py` -> pass.
  - `npm run -w services/app/server build` -> pass.
