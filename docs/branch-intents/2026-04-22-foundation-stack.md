# Branch Intent: foundation stack

## Intent
Create a simple, runnable end-to-end stack for ingest/search/review:
Postgres + Python runner + Node API + React web + nginx.

## Scope
- Add core v1 schema and keep legacy schema intact.
- Add dockerized API/web stack.
- Add Python pipeline for discovery, metrics, descriptions.

## Architecture decisions
- Utility runner container (profile-based) instead of always-on worker.
- Shared TypeScript types package for API + web.
- Relative path + source root storage for portability.

## What worked
- Single compose stack with separate services.
- Basic review UI and API routes functional by design.

## What did not work
- Not implementing semantic vector search in this iteration.
- No websocket stream in this iteration.

## Validation
- Build and type checks are expected to validate runtime wiring.

## Follow-up
- Add pagination metadata totals.
- Add tag/category extraction model and facet filters.
- Add auth only if multi-user needs appear.
