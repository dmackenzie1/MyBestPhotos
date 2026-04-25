# Branch Intent: 2026-04-24-ui-timeline-filters-modernization

## Quick Summary
- Purpose: Improve browse/timeline usability and polish: shared filters in timeline mode, modernized filter controls, clearer sort guidance, less harsh text contrast, icon sizing control, and full-image filename preservation for save/open actions.
- Keywords: ui, timeline, filters, modernization
## Intent
- Improve browse/timeline usability and polish: shared filters in timeline mode, modernized filter controls, clearer sort guidance, less harsh text contrast, icon sizing control, and full-image filename preservation for save/open actions.

## Scope
- In scope:
  - UI updates in `services/app/client/src` for filters, timeline, grid, and layout behavior.
  - API image response header change in `services/app/server/src/index.ts` to preserve filename in full-image responses.
  - Branch-intent record updates for this task.
- Out of scope:
  - Schema migrations or new backend endpoints.
  - Major redesign of app information architecture.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-24-ui-browse-pane-iteration.md`
  - `docs/branch-intents/2026-04-22-tighten-ui-filters-and-metadata.md`
  - `docs/branch-intents/2026-04-22-ui-reference-layout-upgrade.md`
- Relevant lessons pulled forward:
  - Keep UX changes incremental and API-compatible.
  - Validate with targeted frontend/server build checks.
- Rabbit holes to avoid this time:
  - Broad backend rewrites for frontend-specific asks.

## Architecture decisions
- Decision:
  - Reuse the existing `FiltersPane` in both browse and timeline layouts and keep shared query/filter state in `App.tsx`.
  - Add lightweight metadata (`Content-Disposition`) on image responses instead of introducing a new download endpoint.
- Why:
  - Addresses timeline/filter parity and filename preservation with minimal disruption.
- Tradeoff:
  - Timeline still depends on the same paginated photo list state as browse and requires explicit load-more interaction for larger sets.

## Error log (mandatory)
- Exact error message(s):
  - `error: Failed to spawn: `pre-commit``
  - `Caused by: No such file or directory (os error 2)`
- Where seen (command/log/file):
  - `uv run pre-commit run --all-files`
- Frequency or reproducibility notes:
  - Reproducible in this environment; pre-commit binary is missing.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Added shared filters + detail pane around timeline view, sort control/help text for browse/timeline, icon-size slider, and updated filter collapse/reset to icon buttons.
  - Why this was tried:
    - Directly addresses user feedback on timeline filtering, control placement, and modernized UI affordances.
  - Result:
    - Successful code update.
- Attempt 2:
  - Change made:
    - Added `downloadName` query usage in client full-image URLs and server-side `Content-Disposition` filename header.
  - Why this was tried:
    - Preserve source filename when opening/saving full-size image.
  - Result:
    - Successful code update.

## What went right (mandatory)
- Changes stayed additive and mostly localized to UI components/styles and one API handler.

## What went wrong (mandatory)
- Screenshot capture not performed yet because browser screenshot tool is unavailable in this environment.

## Validation (mandatory)
- Commands run:
  - `npm run -w services/app/client build`
  - `npm run -w services/app/server build`
  - `uv run pre-commit run --all-files`
- Observed results:
  - Client and server TypeScript builds passed.
  - pre-commit command failed because pre-commit is not installed in this environment.

## Follow-up
- Next branch goals:
  - Add small tooltip/legend affordance explaining each metric in more depth if users still need more sort clarity.
- What to try next if unresolved:
  - If timeline still feels capped, add dedicated timeline pagination controls and optional larger page size for timeline mode.
