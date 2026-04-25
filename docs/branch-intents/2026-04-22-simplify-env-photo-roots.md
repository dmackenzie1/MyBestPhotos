# Branch Intent: 2026-04-22-simplify-env-photo-roots

## Quick Summary
- Purpose: Simplify environment and compose configuration by removing numbered photo root variables (`PHOTO_ROOT_1..3`) in favor of a single `PHOTO_ROOT` mount and cleaner defaults.
- Keywords: simplify, env, photo, roots
## Intent

Simplify environment and compose configuration by removing numbered photo root variables (`PHOTO_ROOT_1..3`) in favor of a single `PHOTO_ROOT` mount and cleaner defaults.

## Scope

- Update `.env.example` to remove numbered root variables and use:
  - `PHOTO_ROOT=./sample-photos`
  - `PHOTO_INGEST_ROOTS=/photos/library`
- Update `docker-compose.yml` mounts for `app-server` and `python-runner` to use `/photos/library`.
- Update docs (`README.md`, architecture overview) to match the simplified env surface.

## Non-goals

- No schema or API contract changes.
- No frontend behavior changes.
- No migration changes.

## Validation Plan

- Run repo-wide checks with `uv run pre-commit run --all-files`.
- Verify no remaining references to `PHOTO_ROOT_1`, `PHOTO_ROOT_2`, `PHOTO_ROOT_3`.
