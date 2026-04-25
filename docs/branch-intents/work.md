# Branch Intent: work

## Quick Summary
- Branch: `work`
- Purpose: Refresh documentation for branch-intent governance so tiny typo edits can skip intents while substantive work keeps one consolidated branch intent per branch.
- Scan first: Use this branch when adjusting documentation/process rules for branch-intent usage.

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

## Update: 2026-04-25 LM Studio LLM runner 400 response_format errors

## Quick Summary
- Branch: `work`
- Purpose: Fix LLM runner LM Studio request shape and add startup diagnostics for endpoint/model configuration.
- Scan first: Use this update when logs show `HTTP 400 ... 'response_format.type' must be 'json_schema' or 'text'`.

## Intent
- Make the LLM stage compatible with current LM Studio OpenAI-compatible API response-format validation and improve observability at startup.

## Scope
- In scope:
  - `src/photo_curator/pipeline_v1/llm_stage.py` request payload + endpoint normalization + startup logging.
  - Targeted tests for endpoint normalization/content extraction.
- Out of scope:
  - Prompt redesign.
  - Database schema changes.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-24-llm-photo-descriptions-and-semantic-search.md`
  - `docs/branch-intents/2026-04-22-update-lmstudio-default-base-url-to-lan-host.md`
- Relevant lessons pulled forward:
  - Keep runner fixes additive and low-drama.
  - Add logging/diagnostics where endpoint/model mismatches are common.
- Rabbit holes to avoid this time:
  - Broad pipeline refactors unrelated to LM Studio request compatibility.

## Architecture decisions
- Decision:
  - Switch LM Studio `response_format.type` to `text` and continue strict JSON parsing client-side.
  - Normalize base URLs so both `http://127.0.0.1:1234` and `http://127.0.0.1:1234/v1` resolve to `/v1/chat/completions`.
  - Log endpoint/model/timeout/response-format once at stage start.
- Why:
  - User logs show 400 validation on `json_object`; LM Studio requires `json_schema` or `text`.
- Tradeoff:
  - Less server-side JSON-schema enforcement; parsing guardrails remain local.

## Error log (mandatory)
- Exact error message(s):
  - `HTTP 400 Bad Request: {"error":"'response_format.type' must be 'json_schema' or 'text'"}`
- Where seen (command/log/file):
  - User-provided python-runner logs for `photo_curator.pipeline_v1.llm_stage:_call_lmstudio`.
- Frequency or reproducibility notes:
  - Repeats for each photo with retries (attempts 1-3).

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Updated LLM request payload to `response_format: {"type": "text"}` and kept strict `json.loads` validation.
  - Why this was tried:
    - Align with LM Studio validation error text while preserving downstream JSON contract.
  - Result:
    - Request format now matches LM Studio accepted values.
- Attempt 2:
  - Change made:
    - Added endpoint normalization helper and startup info log with endpoint/model/timeout/response format.
  - Why this was tried:
    - User requested early debug visibility and is using base URL without `/v1`.
  - Result:
    - Startup logs now show where requests are posted and with which model.
- Attempt 3:
  - Change made:
    - Added tests for endpoint normalization and structured list-content extraction.
  - Why this was tried:
    - Lock in compatibility behavior and avoid regressions.
  - Result:
    - New tests validate key helper behavior.

## What went right (mandatory)
- Fix is minimal, local to LLM stage, and directly addresses the exact 400 payload validation error.

## What went wrong (mandatory)
- Could not perform full end-to-end LM Studio run in this environment against user-hosted model endpoint.

## Validation (mandatory)
- Commands run:
  - `uv run --project . pytest tests/test_llm_stage.py`
  - `uv run --project . ruff check src/photo_curator/pipeline_v1/llm_stage.py tests/test_llm_stage.py`
- Observed results:
  - Targeted tests and lint checks pass.

## Follow-up
- Next branch goals:
  - If needed, add optional `json_schema` mode behind a config flag for stricter server-side structure.
- What to try next if unresolved:
  - Capture one raw LM Studio response body in debug logs when parse fails to detect model-side non-JSON output patterns.
