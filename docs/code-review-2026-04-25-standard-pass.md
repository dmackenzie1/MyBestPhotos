# Standard Code Review Pass — 2026-04-25

## Executive summary
This pass found one critical runtime blocker, several build/test readiness issues, and a few dead-code/hygiene concerns.

## High-priority findings

1. **Critical syntax error in pipeline run tracking (Python).**
   - `src/photo_curator/pipeline_run.py` has a mis-indented `if null_counts:` block (`notes_parts.append(...)` is not indented), which fails parsing and blocks linting/import.  
   - Observed via `uv run ruff check .`.

2. **Frontend build currently fails due to unresolved router dependency.**
   - TypeScript build errors: `Cannot find module 'react-router-dom'` in client source.
   - Observed via `npm run build`.

3. **Python test collection is not runnable in current setup without additional environment normalization.**
   - Direct run: `photo_curator` import path missing.
   - With `PYTHONPATH=src`: missing runtime dependency (`pydantic`) and missing package-style import for `scripts`.

## Medium-priority findings

4. **Dead/unreferenced UI component: `MapPlaceholder`.**
   - `MapPlaceholder.tsx` exists but has no imports/usages in TS source.

5. **Duplicate generated JS checked into TS source tree.**
   - `services/app/client/src/` contains both `.tsx/.ts` and transpiled `.js` siblings (plus `tsconfig.tsbuildinfo`), increasing drift/confusion risk.

6. **Schema definition duplication risk.**
   - Core schema lives in both `services/postgres/init/001_stock_schema.sql` and `services/postgres/bootstrap.sql` (plus `ALTER TABLE` backfill path).
   - This is intentional for idempotent bootstrap but should be carefully kept synchronized to avoid subtle drift.

## Notable positives

- API route structure is consistently namespaced under `/api/v1`.
- Server query builder centralizes filter/sort logic (`photoQuery.ts`) rather than scattering SQL clause assembly.
- Path traversal hardening exists for image reads (`resolveFilePath` root containment check).

## Suggested remediation order

1. Fix `pipeline_run.py` indentation syntax error.
2. Reconcile Python environment/test execution (`uv sync`, dependency install, import path conventions).
3. Repair frontend workspace dependency state (`react-router-dom` resolution) and re-run build.
4. Remove generated JS/tsbuildinfo from client source tree (or formalize emission location) and delete unreferenced `MapPlaceholder` if unused.
5. Add a lightweight consistency check to keep `init/001_stock_schema.sql` and `bootstrap.sql` aligned.
