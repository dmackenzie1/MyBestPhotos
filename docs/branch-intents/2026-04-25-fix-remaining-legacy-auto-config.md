# Branch Intent: 2026-04-25-fix-remaining-legacy-auto-config

## Quick Summary
- Purpose: Fix the remaining main issue (legacy-only behavior in `select_top` / `score_technical`) by adding schema auto-detection and v1-compatible execution paths.
- Keywords: fix, remaining, legacy, auto, config
## Intent
- Fix the remaining main issue (legacy-only behavior in `select_top` / `score_technical`) by adding schema auto-detection and v1-compatible execution paths.

## Scope
- In scope:
  - Add auto-config mode detection for legacy vs v1 schema in `select_top.py`.
  - Add auto-config mode detection for legacy vs v1 schema in `technical.py`.
  - Keep behavior backward-compatible for existing legacy deployments.
- Out of scope:
  - Full replacement of selection persistence semantics for v1 (no legacy `runs/selections` table equivalent currently).

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-25-audit-stream-consolidated.md`
  - `docs/branch-intents/2026-04-22-validate-external-code-review.md`
- Relevant lessons pulled forward:
  - Keep fixes incremental and avoid broad rewrites.
  - Prefer compatibility bridges when legacy modules are still present.
- Rabbit holes to avoid this time:
  - Reworking unrelated API/UI concerns.

## Architecture decisions
- Decision:
  - Use runtime table detection and select mode-specific SQL for legacy/v1.
- Why:
  - Allows same command code to run in modern schema without manual toggles.
- Tradeoff:
  - v1 `select_top` compatibility mode returns results but does not persist to legacy `runs/selections` tables.

## Error log (mandatory)
- Exact error message(s):
  - None during implementation.
- Where seen (command/log/file):
  - N/A.
- Frequency or reproducibility notes:
  - N/A.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Added schema detection + mode-specific readers in `select_top.py`.
  - Why this was tried:
    - Resolve remaining legacy-table dependency while preserving legacy path.
  - Result:
    - Successful; v1 path now uses `files/file_metrics` and optional `file_llm_results.description_embedding`.
- Attempt 2:
  - Change made:
    - Added schema detection + mode-specific writes in `technical.py`.
  - Why this was tried:
    - Make technical scoring usable in v1 schema without legacy tables.
  - Result:
    - Successful; v1 path writes to `file_metrics` and reports mode in logs.

## What went right (mandatory)
- Backward compatibility retained for legacy environments.
- Ruff format/check succeeded after edits.

## What went wrong (mandatory)
- v1 compatibility mode for `select_top` cannot persist into legacy selection tables by design.

## Validation (mandatory)
- Commands run:
  - `uv run ruff format src/photo_curator/select_top.py src/photo_curator/technical.py`
  - `uv run ruff check src/photo_curator/select_top.py src/photo_curator/technical.py`
- Observed results:
  - Formatting and lint checks passed.

## Follow-up
- Next branch goals:
  - Add a v1-native persisted selection artifact/table if needed.
- What to try next if unresolved:
  - Introduce a `file_selections` table and wire `select_top` persistence there.
