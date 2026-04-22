# Branch Intent: python runner startup gpu cache

## Intent
- Align stack startup with current operating preference: keep Python runner in Docker Compose (not npm), start it with the full stack, and gate it on healthy upstream services.
- Improve runner cold-start behavior and document expected host/GPU/runtime requirements.

## Scope
- In scope:
  - Update `docker-compose.yml` runner service startup order and runtime settings.
  - Add GPU-related runner configuration in compose.
  - Add lightweight runner cache persistence to reduce repeated dependency download/setup latency.
  - Update README startup/runbook guidance for the new runner behavior.
- Out of scope:
  - Reworking runner pipeline internals.
  - Changing Node API route contracts.
  - Replacing Docker Compose with npm-based orchestration.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-foundation-stack.md`
  - `docs/branch-intents/2026-04-22-restructure-services-stack.md`
  - `docs/branch-intents/2026-04-22-fix-compose-connectivity-and-startup.md`
- Relevant lessons pulled forward:
  - Keep service wiring changes minimal and explicit.
  - Prefer compose health-gated startup over ad-hoc sequencing.
  - Update README whenever stack behavior changes.
- Rabbit holes to avoid this time:
  - Frontend/UI refactors unrelated to runner orchestration.
  - API/DB feature additions unrelated to startup and runtime requirements.

## Architecture decisions
- Decision:
  - Keep Python runner containerized and part of the default compose graph, with `depends_on` health gates for Postgres and app-server.
- Why:
  - Runner needs mounted photo files plus container-network access to Postgres/API/LM Studio and optional host GPU support.
- Tradeoff:
  - Runner now participates in default startup instead of profile-only execution, which increases default stack workload.

## Error log (mandatory)
- Exact error message(s):
  - No concrete runtime error provided; task was driven by startup/operability concerns.
- Where seen (command/log/file):
  - User-reported orchestration concerns during local stack operation.
- Frequency or reproducibility notes:
  - N/A (design/flow adjustment request).

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Reviewed current compose and README wiring to confirm runner was profile-only and only gated on Postgres health.
  - Why this was tried:
    - Establish baseline behavior against requested startup pipeline.
  - Result:
    - Confirmed runner was excluded from default `docker compose up` and required manual profile invocation.
- Attempt 2:
  - Change made:
    - Planned compose updates to remove runner profile-only startup, add app-server health dependency, add GPU flags, and persist uv cache volume.
  - Why this was tried:
    - Match requested full-stack and performance behavior while staying incremental.
  - Result:
    - Implemented in compose plus README/runbook updates.

## What went right (mandatory)
- Existing health-check dependency pattern made runner startup ordering change straightforward.
- Cache optimization was achievable without introducing new tooling.

## What went wrong (mandatory)
- Could not verify live GPU attach behavior in this environment (no Docker daemon/GPU runtime validation available).

## Validation (mandatory)
- Commands run:
  - `docker compose config`
- Observed results:
  - Could not run in this environment because Docker CLI is unavailable (`docker: command not found`).

## Follow-up
- Next branch goals:
  - Validate runner startup end-to-end on a GPU-capable Docker host and tune optional fallback mode for non-GPU hosts if needed.
- What to try next if unresolved:
  - Add a documented `PYTHON_RUNNER_GPU_ENABLED` toggle/profile split if teams need easy CPU-only startup without compose edits.
