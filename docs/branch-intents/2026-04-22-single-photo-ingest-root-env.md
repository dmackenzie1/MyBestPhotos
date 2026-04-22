# Branch Intent: 2026-04-22-single-photo-ingest-root-env

## Intent
- Align environment wiring with current runtime plan: one host photo mount for ingest scanning, with no separate multi-root CSV configuration required.

## Scope
- In scope:
  - Replace `PHOTO_ROOT` with `PHOTO_INGEST_ROOT` in Compose mount wiring.
  - Remove `PHOTO_INGEST_ROOTS` from `.env.example` and docs.
  - Keep Python runner ingest target fixed to `/photos/library` in Compose.
- Out of scope:
  - Python config refactors.
  - API contract changes.
  - UI changes.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-simplify-env-photo-roots.md`
  - `docs/branch-intents/2026-04-22-restructure-services-stack.md`
- Relevant lessons pulled forward:
  - Keep env surface simple and avoid extra root vars when one mount is enough.
  - Update docs with Compose/env changes together.
- Rabbit holes to avoid this time:
  - No reintroduction of multi-root env knobs for this branch.

## Architecture decisions
- Decision:
  - Use one host mount variable: `PHOTO_INGEST_ROOT`.
  - Keep runner scan path as `/photos/library` via `PHOTO_CURATOR_DEFAULT_ROOTS` in Compose.
- Why:
  - Matches current operational intent: one ingest library mount.
- Tradeoff:
  - Less flexibility for ad-hoc multi-root runs via `.env`, but clearer defaults and fewer misconfigurations.

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
    - Updated `.env.example`, `docker-compose.yml`, and docs to use `PHOTO_INGEST_ROOT` + `/photos/library` default scan path.
  - Why this was tried:
    - User requested one mount as the ingest root and removal of redundant photo-root wiring.
  - Result:
    - Successful; env and docs now match single-mount ingest model.

## What went right (mandatory)
- Existing compose and docs structure made the env simplification straightforward.

## What went wrong (mandatory)
- No functional errors; only potential confusion risk addressed by docs wording updates.

## Validation (mandatory)
- Commands run:
  - `rg -n "PHOTO_ROOT|PHOTO_INGEST_ROOTS" .env.example docker-compose.yml README.md docs/architecture/stack-overview.md`
  - `uv run pre-commit run --all-files`
- Observed results:
  - Deprecated keys removed from active env/docs wiring.
  - `pre-commit` could not complete in this environment because `uv` failed to fetch from PyPI (`https://pypi.org/simple/loguru/`) after retries.

## Follow-up
- Next branch goals:
  - If multi-root ingest is needed again, define explicit UX and naming first (host mounts vs container scan roots).
- What to try next if unresolved:
  - Add a separate advanced override env var documented as optional only.
