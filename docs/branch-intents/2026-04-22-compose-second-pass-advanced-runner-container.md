# Branch Intent: 2026-04-22-compose-second-pass-advanced-runner-container

## Quick Summary
- Purpose: Address review feedback by creating a real second-pass containerized runner in Docker Compose, with shared source mounts and GPU-capable advanced pass wiring.
- Keywords: compose, second, pass, advanced, runner, container
## Intent
- Address review feedback by creating a real second-pass containerized runner in Docker Compose, with shared source mounts and GPU-capable advanced pass wiring.

## Scope
- In scope:
  - Split compose runner execution into base pass (`python-runner`) and second pass (`python-advanced-runner`).
  - Ensure advanced pass runs after successful base pass completion.
  - Keep both passes containerized with source photo mount access.
  - Wire GPU capability for advanced pass through `docker-compose.prod.yml`.
  - Update docs for new operational commands.
- Out of scope:
  - Changing advanced scoring algorithms.
  - Reworking API behavior.
  - Queue/orchestrator framework changes.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-two-stage-ingest-advanced-nima.md`
  - `docs/branch-intents/2026-04-22-split-compose-base-and-prod-gpu-runner.md`
  - `docs/branch-intents/2026-04-22-python-runner-startup-gpu-cache.md`
- Relevant lessons pulled forward:
  - Keep compose changes explicit and incremental.
  - Put GPU requirements in prod overlay, not base compose.
  - Document startup/runbook changes immediately.
- Rabbit holes to avoid this time:
  - No broader service architecture rewrite.
  - No changes to schema or non-runner business logic.

## Architecture decisions
- Decision:
  - Keep two one-shot runner services:
    - `python-runner` runs `photo-curator base-ingest`
    - `python-advanced-runner` runs `photo-curator advanced-runner`
  - Advanced service depends on base service completion success.
- Why:
  - Gives concrete second-pass separation while preserving the current simple compose orchestration model.
- Tradeoff:
  - Startup command now includes one more service and logs stream to watch.

## Error log (mandatory)
- Exact error message(s):
  - `docker: command not found`
- Where seen (command/log/file):
  - Attempting to validate merged compose config in this environment.
- Frequency or reproducibility notes:
  - Reproducible here due missing Docker CLI in execution environment.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Updated `python-runner` command to only execute base ingest.
  - Why this was tried:
    - Enforce explicit first pass in container orchestration.
  - Result:
    - Successful.
- Attempt 2:
  - Change made:
    - Added `python-advanced-runner` service with matching mounts/env and dependency on base pass completion.
  - Why this was tried:
    - Implement concrete second pass as requested.
  - Result:
    - Successful.
- Attempt 3:
  - Change made:
    - Moved GPU overlay target from `python-runner` to `python-advanced-runner`.
  - Why this was tried:
    - Align GPU capability with advanced/model-style pass.
  - Result:
    - Successful.
- Attempt 4:
  - Change made:
    - Updated README and architecture docs for new split-runner startup/runbook behavior.
  - Why this was tried:
    - Keep operations clear and prevent drift between behavior and docs.
  - Result:
    - Successful.

## What went right (mandatory)
- Compose split was additive and reused existing env/mount patterns.
- Second pass now has an explicit container boundary and startup ordering.

## What went wrong (mandatory)
- Could not run docker-compose validation commands in this environment due missing Docker CLI.

## Validation (mandatory)
- Commands run:
  - `python -m unittest tests/test_ingest_selection.py tests/test_config_ingest_env_aliases.py tests/test_nima_scoring.py`
  - `docker compose -f docker-compose.yml -f docker-compose.prod.yml config`
- Observed results:
  - Python tests passed.
  - Docker compose command could not run here (`docker: command not found`).

## Follow-up
- Next branch goals:
  - Validate full startup sequencing on Docker host and verify advanced pass waits for base completion in practice.
  - Consider adding a dedicated `make run-runners` shortcut for operators.
- What to try next if unresolved:
  - If startup ordering issues appear, add explicit one-shot exit checks and runner health/log markers.
