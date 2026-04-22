# Branch Intent: fix python runner libgl opencv headless

## Intent
- Fix Python runner startup failure caused by missing `libGL.so.1` when importing OpenCV inside the `photo-curator` CLI in Docker.

## Scope
- In scope:
  - Resolve OpenCV import dependency for the containerized runner startup path.
  - Keep CLI/API behavior unchanged while making startup reliable in minimal container images.
- Out of scope:
  - Refactoring image-quality/scoring logic.
  - Adding apt/system package installation layers to the runner image.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-python-runner-startup-gpu-cache.md`
  - `docs/branch-intents/2026-04-22-fix-uv-entrypoint-spawn.md`
- Relevant lessons pulled forward:
  - Keep runner fixes minimal and focused on startup reliability.
  - Avoid broad stack rewiring when a direct packaging fix is sufficient.
- Rabbit holes to avoid this time:
  - Changing Compose service names/ports or orchestration topology.
  - Reworking pipeline internals unrelated to import/runtime loading.

## Architecture decisions
- Decision:
  - Switch from `opencv-python` to `opencv-python-headless` in Python dependencies.
- Why:
  - The headless wheel avoids GUI/X11/OpenGL runtime requirements (`libGL.so.1`) that are unavailable in lean runner containers.
- Tradeoff:
  - GUI-dependent OpenCV features are unavailable, but this project uses file-based image processing (`imread`, resize, colorspace, Laplacian/histogram) that works in headless mode.

## Error log (mandatory)
- Exact error message(s):
  - `ImportError: libGL.so.1: cannot open shared object file: No such file or directory`
- Where seen (command/log/file):
  - Docker compose logs for `mybestphotos-python-runner` during CLI startup/import path.
- Frequency or reproducibility notes:
  - Reproducible at container startup when `photo-curator` imports modules that import `cv2`.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Replaced `opencv-python` with `opencv-python-headless` in `pyproject.toml`.
  - Why this was tried:
    - Remove runtime dependency on host/container OpenGL libraries while preserving OpenCV core image processing APIs.
  - Result:
    - Change applied; pending full container validation in user environment.
- Attempt 2:
  - Change made:
    - Ran local CLI import/startup check command.
  - Why this was tried:
    - Validate that Python package metadata and entrypoint still resolve after dependency change.
  - Result:
    - Command was blocked in this environment by network tunnel access to PyPI (dependency fetch failure), so full runtime verification is still pending.

## What went right (mandatory)
- Dependency-only change keeps patch small and avoids Dockerfile churn.

## What went wrong (mandatory)
- Could not run `docker compose` validation in this environment because Docker CLI/runtime is unavailable.

## Validation (mandatory)
- Commands run:
  - `uv run --project . photo-curator --help`
- Observed results:
  - Command failed before CLI startup due to PyPI fetch connectivity (`Failed to fetch: https://pypi.org/simple/psycopg/`).

## Follow-up
- Next branch goals:
  - Confirm compose startup path on a Docker host with a clean environment.
- What to try next if unresolved:
  - If any OpenCV plugin still requires system libs, add explicit runner image packages in a dedicated Dockerfile and document them.
