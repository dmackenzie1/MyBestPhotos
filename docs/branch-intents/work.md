# Branch Intent: work

## Quick Summary
- Purpose: Refresh documentation for branch-intent governance so tiny typo edits can skip intents while substantive work keeps one consolidated branch intent per branch.
- Keywords: docs, process, branch-intents
## Intent
- Align docs with a practical branch-intent policy: summary-first scanning, one file per branch, and typo/one-line exemptions.

## Scope
- In scope:
  - Update repository policy docs that define branch-intent workflow.
  - Add quick-summary headers to existing branch-intent files for fast triage.
- Out of scope:
  - Non-documentation code behavior changes.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-branch-intent-discipline-docs.md`
  - `docs/branch-intents/2026-04-25-standard-code-review.md`
  - `docs/branch-intents/TEMPLATE.md`
- Relevant lessons pulled forward:
  - Keep intent records concise but explicit about outcomes and next steps.
- Rabbit holes to avoid this time:
  - Avoid creating new process complexity beyond requested governance updates.

## Architecture decisions
- Decision:
  - Introduce a `## Quick Summary` section in the template and backfill existing branch-intent docs.
  - Update governance text in `AGENTS.md`, `coding_rules.txt`, and `docs/README.md` to codify one-file-per-branch + typo/one-line exemption.
- Why:
  - Needed rapid scanability and reduced intent-document churn for tiny edits.
- Tradeoff:
  - Historical files gain boilerplate lines, but become much faster to triage.

## Error log (mandatory)
- Exact error message(s):
  - No runtime error; issue was process friction (too many intent files, hard to scan quickly).
- Where seen (command/log/file):
  - Team workflow feedback in task request.
- Frequency or reproducibility notes:
  - Reproducible each time branches receive many small commits.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Updated template and policy docs.
  - Why this was tried:
    - Make future behavior explicit and consistent for both humans and Codex.
  - Result:
    - Governance language now reflects requested rules.
- Attempt 2:
  - Change made:
    - Backfilled quick-summary headers in existing branch-intent files.
  - Why this was tried:
    - Provide immediate scanability for older branches, not just future ones.
  - Result:
    - Existing intent docs now expose high-level summaries near the top.

## What went right (mandatory)
- Bulk edit was deterministic and kept each file’s original details intact below the new summary section.

## What went wrong (mandatory)
- Some old files had non-bulleted `## Intent` content; initial summary extraction needed a fallback pass.

## Validation (mandatory)
- Commands run:
  - `python - <<'PY' ...` (bulk add quick summaries)
  - `python - <<'PY' ...` (fallback summary cleanup)
- Observed results:
  - All existing branch-intent docs were updated with a top-level quick summary.

## Follow-up
- Next branch goals:
  - Add optional lint/check script to enforce one-file-per-branch naming and required summary headers.
- What to try next if unresolved:
  - Add a CI docs check that flags new branch-intent files missing `## Quick Summary`.

---

## Update: 2026-04-25 Python runner startup regression

## Quick Summary
- Branch: `work`
- Purpose: Fix `python-runner` exiting immediately by restoring its missing compose command/wiring.
- Scan first: Use this update when logs show bare `uv` help output for `python-runner`.

## Intent
- Restore the expected base-ingest one-shot behavior for `python-runner` in `docker-compose.yml`.

## Scope
- In scope:
  - `docker-compose.yml` updates for `python-runner` command + runtime wiring.
  - Branch-intent log update for this same branch file.
- Out of scope:
  - Changes to advanced/LLM runner behavior.
  - Python pipeline code refactors.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-fix-uv-entrypoint-spawn.md`
  - `docs/branch-intents/2026-04-22-python-runner-preflight-double-check.md`
  - `docs/branch-intents/2026-04-22-python-runner-startup-gpu-cache.md`
- Relevant lessons pulled forward:
  - Keep runner fixes minimal and explicit in compose.
  - Prefer health-gated startup and deterministic one-shot commands.
- Rabbit holes to avoid this time:
  - Broader compose/service graph redesign.

## Architecture decisions
- Decision:
  - Re-add `python-runner` service wiring (`depends_on`, volumes, `uv sync` + `base-ingest` command).
- Why:
  - Missing `command` made container run plain `uv`, which only prints help and exits.
- Tradeoff:
  - Runner startup does an explicit `uv sync` each run; slower cold start but robust for dependency drift.

## Error log (mandatory)
- Exact error message(s):
  - `An extremely fast Python package manager.`
  - `Usage: uv [OPTIONS] <COMMAND>`
- Where seen (command/log/file):
  - User-provided `python-runner` container logs.
- Frequency or reproducibility notes:
  - Reproduces whenever `python-runner` has no compose `command`.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Inspected `docker-compose.yml` service block and confirmed `python-runner` ended after environment variables with no `command`.
  - Why this was tried:
    - The log signature matched a default `uv` invocation.
  - Result:
    - Root cause confirmed.
- Attempt 2:
  - Change made:
    - Restored `python-runner` dependencies, mounts, uv cache mount, and command:
      - `uv sync --project . && uv run --project . photo-curator base-ingest`.
  - Why this was tried:
    - Re-establish intended ingest behavior used elsewhere in docs/runbook.
  - Result:
    - Compose config now resolves with a concrete runner command.

## What went right (mandatory)
- Root cause was isolated quickly and fixed with a small compose-only patch.

## What went wrong (mandatory)
- End-to-end container execution cannot be fully validated in this environment without launching Docker services.

## Validation (mandatory)
- Commands run:
  - `docker compose config`
  - `docker compose config | sed -n '/python-runner:/,/python-advanced-runner:/p'`
- Observed results:
  - Compose renders `python-runner.command` as `uv sync --project . && uv run --project . photo-curator base-ingest`.

---

## Update: 2026-04-25 random browse sort option

## Quick Summary
- Branch: `work`
- Purpose: Add a user-facing random sort option in browse/timeline and wire backend query handling.
- Scan first: Use this update when sort dropdown requests include “random”.

## Intent
- Add a straightforward `random` sort mode without changing existing default sort behavior.

## Scope
- In scope:
  - Add `random` in client sort dropdowns.
  - Accept `random` in server query validation and SQL order mapping.
- Out of scope:
  - Reworking pagination semantics for randomized ordering.
  - Changing default sort choice.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-24-remove-filename-sort-option.md`
  - `docs/branch-intents/2026-04-24-ui-browse-pane-iteration.md`
- Relevant lessons pulled forward:
  - Keep the patch focused to sort-option surfaces and avoid unrelated UI/server refactors.
- Rabbit holes to avoid this time:
  - No broad query/pagination redesign.

## Architecture decisions
- Decision:
  - Implement `random` as `ORDER BY RANDOM()` in the server order-by map and expose it in both sort selectors.
- Why:
  - Minimal, direct implementation that matches the request (“just do random on there”).
- Tradeoff:
  - Randomized ordering can reshuffle between pages/requests, so pagination order is non-deterministic by design.

## Error log (mandatory)
- Exact error message(s):
  - None encountered.
- Where seen (command/log/file):
  - N/A.
- Frequency or reproducibility notes:
  - N/A.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Added `random` to client `SORT_OPTIONS` in browse grid and timeline views.
  - Why this was tried:
    - Ensures users can select random in all existing UI sort controls.
  - Result:
    - UI now presents Random sort.
- Attempt 2:
  - Change made:
    - Added `random` to `listQuerySchema.sort` enum and `ORDER_BY_SQL` map.
  - Why this was tried:
    - Allows API requests with `sort=random` to validate and execute.
  - Result:
    - Backend supports random ordering.

## What went right (mandatory)
- Change remained low-drama and localized to sort option definitions + order map.

## What went wrong (mandatory)
- No issues encountered in this pass.

## Validation (mandatory)
- Commands run:
  - `npm run -w services/app/client build`
  - `npm run -w services/app/server build`
- Observed results:
  - Client build failed in this environment due to missing `react-router-dom` type/module resolution in `services/app/client`.
  - Server build completed successfully.
