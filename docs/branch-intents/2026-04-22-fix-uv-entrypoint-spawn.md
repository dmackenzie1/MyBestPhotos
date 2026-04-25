# Branch Intent: 2026-04-22-fix-uv-entrypoint-spawn

## Quick Summary
- Branch: `2026-04-22-fix-uv-entrypoint-spawn`
- Purpose: Fix Python runner startup failure where `uv run` cannot spawn the `photo-curator` CLI entry point.
- Scan first: Use this branch when you are working on the same feature area or error pattern.



## Intent
- Fix Python runner startup failure where `uv run` cannot spawn the `photo-curator` CLI entry point.

## Scope
- In scope:
  - Confirm root cause of `Failed to spawn: photo-curator` in current project metadata.
  - Update packaging metadata so `project.scripts` entry points are installable by `uv`.
  - Validate command behavior as far as environment permits.
- Out of scope:
  - Compose stack rewiring.
  - Runtime pipeline behavior changes unrelated to CLI spawning.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-python-runner-startup-gpu-cache.md`
  - `docs/branch-intents/2026-04-22-fix-compose-connectivity-and-startup.md`
- Relevant lessons pulled forward:
  - Keep startup fixes minimal and explicit.
  - Document environment limitations during validation.
- Rabbit holes to avoid this time:
  - Runner orchestration changes unrelated to package/entrypoint metadata.

## Architecture decisions
- Decision:
  - Add explicit Python packaging metadata (`build-system`) and src-layout wheel configuration in `pyproject.toml` so `uv` can install `project.scripts`.
- Why:
  - `project.scripts` are currently defined, but `uv` warns the project is not packaged and skips entry point installation.
- Tradeoff:
  - Introduces build backend config (`hatchling`) but keeps runtime code unchanged.

## Error log (mandatory)
- Exact error message(s):
  - `warning: Skipping installation of entry points (project.scripts) because this project is not packaged; to install entry points, set tool.uv.package = true or define a build-system`
  - `error: Failed to spawn: photo-curator`
  - `Caused by: No such file or directory (os error 2)`
- Where seen (command/log/file):
  - User-reported Python runner output.
- Frequency or reproducibility notes:
  - Reproducible when invoking script entry point through `uv run` against current metadata.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Reproduced local command path with `uv run --project . photo-curator --help`.
  - Why this was tried:
    - Confirm current environment behavior before patching.
  - Result:
    - Blocked by outbound network restrictions while resolving dependencies; still consistent with metadata-level root cause from warning text.
- Attempt 2:
  - Change made:
    - Planned metadata patch to add `build-system` plus hatch src-package mapping.
  - Why this was tried:
    - Make `uv` treat project as package and install script entry points.
  - Result:
    - Implemented; pending full runtime verification in network-enabled environment.

## What went right (mandatory)
- Root cause is directly identified in uv warning text and maps to missing package metadata.

## What went wrong (mandatory)
- Full command validation is limited by restricted network access in this environment.

## Validation (mandatory)
- Commands run:
  - `uv run --project . photo-curator --help`
- Observed results:
  - Dependency fetch failed due to network tunnel restrictions before command execution.

## Follow-up
- Next branch goals:
  - Re-run `uv run --project . photo-curator --help` in normal networked dev host.
- What to try next if unresolved:
  - Add `[tool.uv] package = true` in addition to build metadata if local uv version still skips script installation.
