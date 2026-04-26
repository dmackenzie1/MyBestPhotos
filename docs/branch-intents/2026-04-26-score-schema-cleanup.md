# Branch Intent: 2026-04-26-score-schema-cleanup

## Quick Summary
- Purpose: Fix mixed score scales (0-1 vs 0-100), rename LLM fields to avoid ambiguity, add LLM columns to file_metrics, normalize all API responses to 0-1, fix search bar width and icon in UI.
- Keywords: scoring, schema, cleanup, normalization, LLM, aesthetic

## Intent
- Eliminate the confusing dual-use of `aesthetic_score` across two tables with different scales.
- Add `llm_aesthetic_score` and `llm_wall_art_score` columns to `file_metrics` so all scores live in one table.
- Normalize all score fields returned by the API to 0-1 range.
- Fix the oversized search input in the TopBar (was filling ~80% of screen width).

## Scope
- In scope:
  - Schema migration: add columns, rename LLM table columns, migrate data.
  - Backend: update all SQL queries and coalesce logic to use new field names; normalize LLM scores to 0-1 in API responses.
  - Shared types: update `PhotoListItem` and `PhotoDetail.metrics` to reflect new fields.
  - Frontend: fix TopBar search width, replace text with minimal SVG icon.
  - Documentation: update scoring-model.md with current architecture and score ranges.
- Out of scope:
  - Redesigning the timeline view.
  - Adding new scoring algorithms or changing existing weights.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-23-clip-aesthetic-scoring-primary-schema.md` — CLIP replaced NIMA; aesthetic_score in file_metrics is now CLIP-derived (0-1).
  - `docs/branch-intents/2026-04-24-llm-photo-descriptions-and-semantic-search.md` — LLM added aesthetic_score and wall_art_score to file_llm_results on 0-100 scale.
- Relevant lessons pulled forward:
  - Keep changes additive where possible; use idempotent ALTER TABLE in bootstrap.sql.
  - Document score scales explicitly to prevent future confusion.
- Rabbit holes to avoid this time:
  - Don't redesign the UI beyond what's broken (search bar width, icon).
  - Don't change scoring weights or formulas.

## Architecture decisions
- Decision: Add `llm_aesthetic_score` and `llm_wall_art_score` columns to `file_metrics` instead of keeping them only in `file_llm_results`.
- Why: Eliminates the need for cross-table coalesce fallbacks; all scores live in one table.
- Tradeoff: Slightly wider file_metrics table, but simpler queries and no scale ambiguity.

## Error log (mandatory)
- Exact error message(s):
  - No runtime errors — this is a data model cleanup. The issue is that `aesthetic_score` has different scales in two tables (0-1 vs 0-100), causing inconsistent API responses when coalesce picks between them.
- Where seen:
  - `services/app/server/src/index.ts` lines 267 and 341 — `coalesce(flm.aesthetic_score, fm.aesthetic_score)` returns different scales depending on which table has data.
  - Database inspection confirmed: file_metrics.aesthetic_score range is ~0.47-0.68 (CLIP-derived), file_llm_results.aesthetic_score range is 10-85 (LLM-generated).

## Attempts made (mandatory)
- Attempt 1:
  - Change made: Add llm_aesthetic_score and llm_wall_art_score to file_metrics, rename columns in file_llm_results, migrate data.
  - Why this was tried: Consolidate all scores into one table with clear naming.
  - Result: Pending — will validate after rebuild.

## What went right (mandatory)
- N/A — work in progress.

## What went wrong (mandatory)
- N/A — work in progress.

## Validation (mandatory)
- Commands to run:
  - `docker compose exec mybestphotos-postgres psql -U photo_curator -d photo_curator -c "SELECT llm_aesthetic_score, llm_wall_art_score FROM file_metrics LIMIT 5;"`
  - `npm run build:server && npm run build:client`
  - Verify API returns consistent 0-1 scores via `curl http://localhost:8080/api/v1/photos | jq '.items[0].aestheticScore'`

## Follow-up
- Next branch goals:
  - Consider whether LLM wall_art_score should influence the curation_score formula.
  - Add score normalization tests for edge cases (NULL, negative values).
