# Branch Intent: 2026-04-24-complete-code-review-pass-2

## Quick Summary
- Purpose: Execute a focused, high-value subset of the requested full code review by reducing backend route complexity, removing duplicated query-shaping logic, and tightening file/path validation without changing API behavior.
- Keywords: complete, code, review, pass, 2
## Intent
- Execute a focused, high-value subset of the requested full code review by reducing backend route complexity, removing duplicated query-shaping logic, and tightening file/path validation without changing API behavior.

## Scope
- In scope:
  - Refactor the API query/filter/sort schema logic into a dedicated module.
  - Reduce size/complexity pressure in `services/app/server/src/index.ts`.
  - Fix defensive checks for photo image route ID parsing and path traversal guard semantics.
  - Validate with TypeScript build.
- Out of scope:
  - Full repo-wide architectural rewrite.
  - Database schema migrations/removals.
  - Frontend style-system consolidation.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-24-full-code-review-hygiene-pass.md`
  - `docs/branch-intents/2026-04-22-fix-review-actionable-items.md`
- Relevant lessons pulled forward:
  - Keep this pass incremental and behavior-preserving.
  - Avoid sweeping multi-service redesign in one patch.
- Rabbit holes to avoid this time:
  - Broad schema churn and end-to-end pipeline rewrites.

## Architecture decisions
- Decision:
  - Extract reusable photo list query/filter/sort definitions into `photoQuery.ts`.
- Why:
  - Keeps route file focused on HTTP orchestration and reduces long-file complexity.
- Tradeoff:
  - Adds one module import, but centralizes query behavior and improves maintainability.

## Error log (mandatory)
- Exact error message(s):
  - `npm warn Unknown env config "http-proxy". This will stop working in the next major version of npm.`
- Where seen (command/log/file):
  - `npm run -w services/app/server build`
- Frequency or reproducibility notes:
  - Reproducible warning; non-blocking for current build.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Added `services/app/server/src/photoQuery.ts` and moved list/status query schemas plus filter and sort SQL mapping into the new module.
  - Why this was tried:
    - To split oversized route concerns into a dedicated component and remove duplication.
  - Result:
    - Successful.
- Attempt 2:
  - Change made:
    - Tightened `resolveFilePath` root-boundary checks and added invalid-ID guard in `/api/v1/photos/:id/image`.
  - Why this was tried:
    - To improve backend safety/correctness uncovered during review.
  - Result:
    - Successful.

## What went right (mandatory)
- The main server entrypoint now delegates query-shaping logic, reducing internal branching complexity.
- Build validation passed after refactor.

## What went wrong (mandatory)
- Did not complete every requested area (DB field audit/frontend style consolidation) in this single patch.

## Validation (mandatory)
- Commands run:
  - `npm run -w services/app/server build`
- Observed results:
  - TypeScript build passed; only non-blocking npm warning about env config.

## Follow-up
- Next branch goals:
  - Continue splitting large route handlers into smaller modules (`health`, `facets`, `detail` mapping helpers).
- What to try next if unresolved:
  - Add targeted API tests for filter/status combinations and image route safety behavior.
