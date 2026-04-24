# Branch Intent: 2026-04-24-full-code-review-hygiene-pass

## Intent
- Perform a repo-wide hygiene pass focused on dead code removal, naming/readability polish, and low-risk correctness cleanups without changing user-facing behavior.

## Scope
- In scope:
  - Run static checks and targeted build/test commands.
  - Remove clearly unused variables/imports and placeholder logic that adds no behavior.
  - Record validation outcomes and environment gaps.
- Out of scope:
  - Functional redesigns, schema migrations, or API contract changes.
  - Broad refactors across unrelated modules.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-fix-review-actionable-items.md`
  - `docs/branch-intents/2026-04-24-full-pass-deferred-advanced-rescore.md`
- Relevant lessons pulled forward:
  - Keep edits incremental and locally verifiable.
  - Avoid mixing cleanup with broad architectural changes.
- Rabbit holes to avoid this time:
  - Deep schema/compose rewrites and speculative performance work.

## Architecture decisions
- Decision:
  - Treat Ruff findings as the source of truth for dead-code cleanup and keep behavior-preserving edits only.
- Why:
  - Automated findings provide objective, low-risk opportunities aligned with the review request.
- Tradeoff:
  - Some potential quality issues remain out of scope if they require functional changes.

## Error log (mandatory)
- Exact error message(s):
  - `error: Failed to spawn: \`pre-commit\`\n  Caused by: No such file or directory (os error 2)`
  - `ModuleNotFoundError: No module named 'photo_curator'`
  - `ModuleNotFoundError: No module named 'pydantic'`
- Where seen (command/log/file):
  - `uv run pre-commit run --all-files`
  - `uv run --project . pytest -q`
  - `PYTHONPATH=src:. uv run --project . pytest -q`
- Frequency or reproducibility notes:
  - Reproducible in this environment during the current task.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Ran `ruff check` and cleaned unused variables/imports plus placeholder no-op logic and an unnecessary f-string.
  - Why this was tried:
    - Directly addresses dead code and readability issues with minimal risk.
  - Result:
    - Successful; Ruff violations resolved.
- Attempt 2:
  - Change made:
    - Ran Python tests and workspace TypeScript builds to validate no regressions.
  - Why this was tried:
    - Verify quality across Python and JS/TS parts of the monorepo.
  - Result:
    - TS builds pass; Python tests blocked by missing environment packages/import-path setup.

## What went right (mandatory)
- Identified and removed several concrete dead-code patterns without changing runtime behavior.
- Workspace builds for shared/server/client succeeded.

## What went wrong (mandatory)
- Default test environment lacks required Python packaging setup/dependencies for pytest collection.

## Validation (mandatory)
- Commands run:
  - `uv run pre-commit run --all-files`
  - `uv run --project . ruff check src tests scripts`
  - `uv run --project . pytest -q`
  - `PYTHONPATH=src:. uv run --project . pytest -q`
  - `npm run build`
- Observed results:
  - Ruff passes after cleanup edits.
  - Python tests fail in collection because environment dependencies/import path are incomplete.
  - Workspace TypeScript build succeeds.

## Follow-up
- Next branch goals:
  - Stabilize Python local test bootstrap (`uv sync`/documented test env) so pytest collection works out of the box.
- What to try next if unresolved:
  - Add a documented canonical test command that sets required `PYTHONPATH` and ensures all runtime deps are installed.
