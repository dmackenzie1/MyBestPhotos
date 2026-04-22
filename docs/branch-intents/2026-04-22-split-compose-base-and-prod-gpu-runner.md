# Branch Intent: split compose base and prod gpu runner

## Intent
- Address feedback on the previous runner wiring by splitting GPU-specific runner settings into a production-style compose override instead of forcing GPU config in the base compose file.

## Scope
- In scope:
  - Keep default compose startup behavior for python-runner in base stack.
  - Move GPU runtime settings into a separate compose override file (`docker-compose.prod.yml`).
  - Update documentation to show base vs prod/GPU compose usage.
  - Record this attempt and lessons in branch-intent docs.
- Out of scope:
  - Changing runner pipeline code.
  - Introducing npm-managed runner orchestration.
  - API/DB schema changes.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-python-runner-startup-gpu-cache.md`
  - `docs/branch-intents/2026-04-22-fix-compose-connectivity-and-startup.md`
  - `docs/branch-intents/2026-04-22-restructure-services-stack.md`
- Relevant lessons pulled forward:
  - Keep compose changes explicit and minimal.
  - Preserve health-gated startup semantics.
  - Document operational command changes immediately in README.
- Rabbit holes to avoid this time:
  - Re-architecting service layout.
  - Forcing GPU requirements in all environments.

## Architecture decisions
- Decision:
  - Keep `docker-compose.yml` as base/default and add `docker-compose.prod.yml` as GPU overlay.
- Why:
  - Base runs should work across wider environments, while prod/GPU hosts can opt into NVIDIA runtime settings.
- Tradeoff:
  - Operators must choose the correct compose command when GPU mode is desired.

## Error log (mandatory)
- Exact error message(s):
  - Prior change risk: hard `gpus: all` can fail on non-GPU hosts/runtimes.
- Where seen (command/log/file):
  - User feedback on previous PR direction.
- Frequency or reproducibility notes:
  - Environment-dependent; likely reproducible on hosts without NVIDIA container runtime.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Kept runner startup/health ordering in base compose and removed mandatory GPU flags from base.
  - Why this was tried:
    - Prevent non-GPU environments from failing default startup.
  - Result:
    - Base compose now remains portable while preserving runner lifecycle behavior.
- Attempt 2:
  - Change made:
    - Added `docker-compose.prod.yml` with GPU-specific runner settings and documented base/prod commands.
  - Why this was tried:
    - Align with “base vs prod” operational split requested in feedback.
  - Result:
    - GPU requirements are explicit and opt-in using compose file layering.

## What went right (mandatory)
- Existing compose structure allowed clean override layering for only runner GPU fields.

## What went wrong (mandatory)
- Docker CLI is unavailable in this environment, so compose merge validation could not be executed locally.

## Validation (mandatory)
- Commands run:
  - `git diff --check`
  - `docker compose -f docker-compose.yml -f docker-compose.prod.yml config`
- Observed results:
  - Whitespace check passes.
  - Docker command could not run here (`docker: command not found`).

## Follow-up
- Next branch goals:
  - Validate both base and prod compose startup on a Docker-enabled machine.
- What to try next if unresolved:
  - Add a lightweight `make up-base` / `make up-prod` wrapper for consistent operator usage.
