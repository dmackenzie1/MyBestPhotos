# Branch Intent: restructure services stack

## Intent
Restructure the project around `services/app`, `services/nginx`, and `services/postgres` while improving UI polish and enabling API stub mode for rapid iteration.

## Scope
- Move app server/client under `services/app`.
- Keep top-level Docker Compose.
- Add docs and reference directories.
- Improve frontend styling toward inspiration image.

## Architecture decisions
- Support both mounted host roots (`PHOTO_ROOT_1..3`) and runtime root list (`PHOTO_ROOTS_JSON`).
- Keep Python runner as profile-based utility service.
- Add `STUB_MODE` to backend so frontend can run without live ingest data.

## What worked
- Clean directory structure is easier to navigate.
- Stub mode keeps UI and API integration moving even before DB data exists.

## What did not work
- Environment did not allow full npm/docker validation in this iteration.

## Validation
- Python compile check succeeded.
- NPM and Docker checks were limited by environment availability/network policy.

## Follow-up
- Add real pagination totals and richer facets.
- Add UI screenshot pipeline to CI artifacts when browser tooling is available.
