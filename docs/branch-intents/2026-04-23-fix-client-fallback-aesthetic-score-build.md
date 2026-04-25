# Branch Intent: 2026-04-23-fix-client-fallback-aesthetic-score-build

## Quick Summary
- Branch: `2026-04-23-fix-client-fallback-aesthetic-score-build`
- Purpose: Fix the frontend TypeScript build failure by aligning demo fallback objects with the current shared `PhotoListItem` and `PhotoDetail` metric types.
- Scan first: Use this branch when you are working on the same feature area or error pattern.



## Intent
- Fix the frontend TypeScript build failure by aligning demo fallback objects with the current shared `PhotoListItem` and `PhotoDetail` metric types.

## Scope
- In scope:
  - Update `services/app/client/src/ui/lib/fallbackData.ts` with required `aestheticScore` fields.
  - Validate frontend build for `services/app/client`.
- Out of scope:
  - Backend API/schema changes.
  - UI behavior or styling changes.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-fix-client-importmeta-env.md`
  - `docs/branch-intents/2026-04-22-ui-componentization-rules.md`
- Relevant lessons pulled forward:
  - Keep frontend fixes narrow and API/type compatible.
  - Validate with targeted client build command.
- Rabbit holes to avoid this time:
  - Reworking Vite/TypeScript config when the error is a concrete type mismatch in fallback data.

## Architecture decisions
- Decision:
  - Add `aestheticScore` directly to fallback list item and fallback metrics object.
- Why:
  - `@mybestphotos/shared` now requires `aestheticScore` in both locations; fallback data must satisfy those contracts for local/demo builds.
- Tradeoff:
  - Requires manual updates whenever shared model fields change, but keeps fallback payloads explicit and realistic.

## Error log (mandatory)
- Exact error message(s):
  - `src/ui/lib/fallbackData.ts(4,3): error TS2741: Property 'aestheticScore' is missing in type ... but required in type 'PhotoListItem'.`
  - `src/ui/lib/fallbackData.ts(37,3): error TS2741: Property 'aestheticScore' is missing in type ... but required in type ... metrics ...`.
- Where seen (command/log/file):
  - `npm run -w services/app/client build` output.
- Frequency or reproducibility notes:
  - Reproducible on every local build before patch.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Reproduced build failure and traced required field definition in `packages/shared/src/index.ts`.
  - Why this was tried:
    - Confirm the source of truth for required properties before changing fallback objects.
  - Result:
    - Successful root-cause confirmation.
- Attempt 2:
  - Change made:
    - Added `aestheticScore` to fallback list item and fallback detail metrics.
  - Why this was tried:
    - Satisfy compile-time requirements from shared types with minimal surface-area change.
  - Result:
    - Successful; client build passes.

## What went right (mandatory)
- Error was isolated quickly to a schema drift between shared types and fallback fixtures.
- Minimal one-file change restored build health.

## What went wrong (mandatory)
- Fallback fixtures were not updated when shared types gained `aestheticScore`, causing avoidable CI/dev build breakage.

## Validation (mandatory)
- Commands run:
  - `npm run -w services/app/client build`
- Observed results:
  - Build now completes successfully with `tsc -b && vite build`.

## Follow-up
- Next branch goals:
  - Consider adding a lightweight fixture/type contract test to catch future shared-type drift earlier.
- What to try next if unresolved:
  - If similar errors recur, run `tsc --pretty false --noEmit` in the client workspace and update fallback fixtures to match `@mybestphotos/shared`.
