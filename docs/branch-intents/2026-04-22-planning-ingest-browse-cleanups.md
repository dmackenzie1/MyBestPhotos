# Branch Intent: 2026-04-22-planning-ingest-browse-cleanups

## Intent
- Plan and implement high-value, low-risk product cleanup items across ingest and browsing UX: configurable ingest limiting, safer photo list scaling, search reset behavior, and non-broken timeline/map placeholders.

## Scope
- In scope:
  - Review architecture/docs and current implementation paths for ingest, scoring, browse, filters, search, and placeholders.
  - Add env-configurable ingest limiting strategy for test runs.
  - Improve browse list loading beyond fixed 120 items.
  - Fix search-clear empty state bug in UI behavior.
  - Add intentional timeline/map placeholder states.
  - Tighten obvious copy/UX wording rough edges.
- Out of scope:
  - Full schema migration or broad ORM adoption.
  - Full timeline/map feature implementation.
  - Large scoring model overhaul.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-ingest-consistency-and-db-lifecycle.md`
  - `docs/branch-intents/2026-04-22-fix-review-actionable-items.md`
- Relevant lessons pulled forward:
  - Keep changes incremental and avoid schema-wide refactors.
  - Prefer changes that are directly verifiable with targeted checks.
- Rabbit holes to avoid this time:
  - Avoid full `photos` vs `files` legacy contract unification in this branch.

## Architecture decisions
- Decision:
  - Keep direct SQL/table-definition approach for now, and add incremental API/UI/pipeline improvements on top.
- Why:
  - Delivers immediate user-visible value without destabilizing working stack.
- Tradeoff:
  - Some duplicated query mapping remains until a later consolidation effort.

## Error log (mandatory)
- Exact error message(s):
  - `npm warn Unknown env config "http-proxy". This will stop working in the next major version of npm.`
  - `ModuleNotFoundError: No module named 'photo_curator'`
  - `AssertionError: Lists differ ...` (test assumed filesystem traversal order)
- Where seen (command/log/file):
  - During `npm run -w services/app/server build` and `npm run -w services/app/client build`.
  - During `python -m unittest tests/test_ingest_selection.py` before setting `PYTHONPATH=src`.
- Frequency or reproducibility notes:
  - Consistent warning in this environment; builds still succeed.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Added ingest limiting configuration fields and deterministic/random candidate selection in discover stage.
  - Why this was tried:
    - Enable fast test runs on large libraries without changing CLI surface.
  - Result:
    - Successful.
- Attempt 2:
  - Change made:
    - Added API list `total`/`hasMore` response and camera model filtering support.
  - Why this was tried:
    - Support scalable UI loading and richer filter controls.
  - Result:
    - Successful.
- Attempt 3:
  - Change made:
    - Reworked browse UI with load-more pagination, robust selected-photo reset behavior, camera/date filters, and timeline/map/settings placeholders.
  - Why this was tried:
    - Address the 120-item browse cap, search-clear empty-state bug, and dead-end pages in one low-risk frontend pass.
  - Result:
    - Successful.
- Attempt 4:
  - Change made:
    - Refactored API list filter construction into one helper used by both list and count queries, then added category/topic filtering and category facets.
  - Why this was tried:
    - Reduce filter/count drift risk and unlock metadata-driven discovery with existing `description_json.categories`.
  - Result:
    - Successful.
- Attempt 5:
  - Change made:
    - Hardened ingest selection with non-negative limit validation and reservoir sampling for random strategy; added unit tests for ingest subset selection behavior.
  - Why this was tried:
    - Improve reliability and scalability under very large file counts while keeping deterministic sampling via seed.
  - Result:
    - Successful after adjusting tests to avoid filesystem iteration-order assumptions.

- Attempt 6:
  - Change made:
    - Added interpretable scoring split fields (`technical_quality_score`, `semantic_relevance_score`, `curation_score`) in schema, pipeline writes, API responses, and client display/sort.
  - Why this was tried:
    - Deliver the requested scoring improvement with minimal architectural risk and without ORM refactors.
  - Result:
    - Successful.

## What went right (mandatory)
- Changes were additive and localized; no schema migration required.
- Build/lint checks passed after formatting.

## What went wrong (mandatory)
- No dedicated browser screenshot tool was available in this run, so visual artifact capture could not be completed here.

## Validation (mandatory)
- Commands run:
  - `ruff format src/photo_curator/config.py src/photo_curator/pipeline_v1.py tests/test_ingest_selection.py`
  - `ruff check src/photo_curator/config.py src/photo_curator/pipeline_v1.py tests/test_ingest_selection.py`
  - `python -m unittest tests/test_ingest_selection.py` (fails without `PYTHONPATH`)
  - `PYTHONPATH=src python -m unittest tests/test_ingest_selection.py`
  - `npm run -w services/app/server build`
  - `npm run -w services/app/client build`
- Observed results:
  - Ruff formatting/check succeeded.
  - Ingest-selection tests pass when run with `PYTHONPATH=src`.
  - Server/client TypeScript builds succeeded.
  - NPM emitted a non-blocking environment warning about `http-proxy` config.

## Follow-up
- Next branch goals:
  - Add integration tests validating curation score flow from pipeline to API list sorting.
  - Add cursor/infinite-scroll option if load-more UX proves insufficient.
  - Introduce a dedicated scored-rank field that separates technical, semantic, and curation components.
  - Add API-level tests for list endpoint filter/pagination combinations.
- What to try next if unresolved:
  - If list queries become heavy at scale, add keyset/cursor pagination and covering indexes for active sort/filter combinations.
