# Branch Intent: 2026-04-22-ui-componentization-rules

## Quick Summary
- Branch: `2026-04-22-ui-componentization-rules`
- Purpose: Refactor the client UI so `App.tsx` is smaller and each major UI block has its own component file and stylesheet.
- Scan first: Use this branch when you are working on the same feature area or error pattern.



## Intent
- Refactor the client UI so `App.tsx` is smaller and each major UI block has its own component file and stylesheet.
- Establish explicit local rules for component/style organization.

## Scope
- In scope:
  - `services/app/client/src/App.tsx` orchestration-focused refactor.
  - New client UI component files and per-component CSS files.
  - New client UI organization rules doc.
  - Branch intent record for this task.
- Out of scope:
  - Backend API or schema changes.
  - New feature behavior outside existing browse/timeline/settings/map scope.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-ui-reference-layout-upgrade.md`
  - `docs/branch-intents/2026-04-22-ui-screenshot-tooling.md`
- Relevant lessons pulled forward:
  - Keep the UI work additive and API-compatible.
  - Keep changes verifiable with targeted client build checks.
- Rabbit holes to avoid this time:
  - Reworking backend contracts just to support structural frontend refactor.

## Architecture decisions
- Decision:
  - Split UI into a `src/ui/` area: `components/`, `styles/`, `lib/`, and shared `types.ts`.
- Why:
  - This keeps files small, keeps responsibilities obvious, and lets component-specific styles evolve without growing a single monolithic stylesheet.
- Tradeoff:
  - More files to navigate, but each file has tighter scope and lower cognitive load.

## Error log (mandatory)
- Exact error message(s):
  - None.
- Where seen (command/log/file):
  - N/A.
- Frequency or reproducibility notes:
  - N/A.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Extracted topbar/filters/grid/detail/timeline/settings/map into separate components with dedicated CSS files.
  - Why this was tried:
    - User requested component-per-file and style-per-component organization.
  - Result:
    - Successful.
- Attempt 2:
  - Change made:
    - Added `src/ui/UI_RULES.md` and reorganized shared helpers/types into `src/ui/lib` + `src/ui/types.ts`.
  - Why this was tried:
    - User asked to “set some rules” for this cleanup direction.
  - Result:
    - Successful.

## What went right (mandatory)
- `App.tsx` now acts as orchestration instead of owning all markup and style concerns.
- The UI behavior remains unchanged while structure is cleaner and easier to extend.

## What went wrong (mandatory)
- Styles still rely on shared class names and global variables, so this is not full CSS-module isolation.

## Validation (mandatory)
- Commands run:
  - `npm run -w services/app/client build`
- Observed results:
  - Build completed successfully.

## Follow-up
- Next branch goals:
  - Convert class naming to stricter namespace prefixes by component.
  - Add lightweight UI tests for key component render paths.
- What to try next if unresolved:
  - Introduce CSS modules incrementally for high-churn components.
