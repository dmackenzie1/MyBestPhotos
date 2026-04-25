# Branch Intent: 2026-04-22-python-runner-preflight-double-check

## Quick Summary
- Branch: `2026-04-22-python-runner-preflight-double-check`
- Purpose: Do a broad reliability double-check of Python runner pathing, network assumptions, and configuration readiness.
- Scan first: Use this branch when you are working on the same feature area or error pattern.



## Intent
- Do a broad reliability double-check of Python runner pathing, network assumptions, and configuration readiness.
- Add a lightweight, runnable preflight check + unit tests so operators can validate setup before attempting full pipeline runs.

## Scope
- In scope:
  - Audit compose and Python runner config surfaces for network/path assumptions.
  - Add a preflight diagnostics script for DB DSN parsing, mount path checks, and optional TCP probes.
  - Add unit tests for the new diagnostics helper logic.
  - Record environment validation outcomes from commands run in this branch.
- Out of scope:
  - Rewriting runner pipeline internals.
  - Rewiring compose service graph.
  - Adding external test frameworks/dependencies.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-python-runner-startup-gpu-cache.md`
  - `docs/branch-intents/2026-04-22-fix-uv-entrypoint-spawn.md`
  - `docs/branch-intents/2026-04-22-fix-python-runner-libgl-opencv-headless.md`
- Relevant lessons pulled forward:
  - Keep runner changes minimal and operationally focused.
  - Document environment limitations clearly when network/docker validation is blocked.
  - Prefer explicit diagnostics over hidden failure modes.
- Rabbit holes to avoid this time:
  - Compose topology changes and unrelated frontend/API refactors.

## Architecture decisions
- Decision:
  - Introduce a stdlib-only `scripts/python_runner_doctor.py` preflight tool.
- Why:
  - It can run without resolving project Python dependencies, useful in constrained/offline environments and fast triage workflows.
- Tradeoff:
  - The doctor check validates connectivity/path/config assumptions, but does not execute full pipeline dependencies (OpenCV/CLIP/DB queries).

## Error log (mandatory)
- Exact error message(s):
  - `error: Failed to fetch: https://pypi.org/simple/numpy/`
  - `Caused by: Request failed after 3 retries`
  - `Caused by: tunnel error: unsuccessful`
- Where seen (command/log/file):
  - `uv run --project . photo-curator --help`
  - `uv run --project . pytest -q`
- Frequency or reproducibility notes:
  - Reproducible in this environment for dependency resolution attempts against PyPI.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Ran direct runner/pytest commands with `uv` to verify current startup testability.
  - Why this was tried:
    - Confirm whether full runner command and unit tests can execute as-is.
  - Result:
    - Blocked by external dependency fetch failures to PyPI.
- Attempt 2:
  - Change made:
    - Added `scripts/python_runner_doctor.py` and `tests/test_python_runner_doctor.py`, plus README usage docs.
  - Why this was tried:
    - Provide an immediate verification path for network/path/config concerns and local unit coverage that does not require third-party dependencies.
  - Result:
    - Script/tests added and validated with `python` + `unittest`.

## What went right (mandatory)
- Added deterministic preflight checks that run quickly and flag likely runner misconfiguration points before full startup.
- Unit tests pass using stdlib test runner in this environment.

## What went wrong (mandatory)
- Could not validate `uv run` or dependency-backed pytest due to PyPI tunnel/connectivity issues.

## Validation (mandatory)
- Commands run:
  - `uv run --project . photo-curator --help`
  - `uv run --project . pytest -q`
  - `python scripts/python_runner_doctor.py --skip-network`
  - `python -m unittest -q tests/test_python_runner_doctor.py`
- Observed results:
  - `uv` commands fail during PyPI dependency fetch in this environment.
  - Doctor script and new unit tests execute successfully.

## Follow-up
- Next branch goals:
  - Run full `uv sync` + `photo-curator pipeline` + pytest in a network-enabled environment.
- What to try next if unresolved:
  - Add optional mirror/index configuration for `uv` in constrained networks and document it in runbooks.
