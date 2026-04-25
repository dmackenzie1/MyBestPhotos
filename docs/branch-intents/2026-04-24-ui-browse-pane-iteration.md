# Branch Intent: 2026-04-24-ui-browse-pane-iteration

## Quick Summary
- Purpose: Apply a focused browse-UI iteration: relocate sort/filter control into the photo pane header, make the filter pane collapsible, keep the detail preview pane visible while scrolling, tighten card density/buttons, add quick per-photo actions, and remove map/settings UI surface.
- Keywords: ui, browse, pane, iteration
## Intent
- Apply a focused browse-UI iteration: relocate sort/filter control into the photo pane header, make the filter pane collapsible, keep the detail preview pane visible while scrolling, tighten card density/buttons, add quick per-photo actions, and remove map/settings UI surface.

## Scope
- In scope:
  - React client layout/interaction updates in `services/app/client/src/App.tsx` and browse components/styles.
  - Server query support for print-score max range filter in `services/app/server/src/index.ts`.
  - Branch-intent logging for this task.
- Out of scope:
  - New backend routes or schema changes.
  - Reintroducing map/settings experiences.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-ui-reference-layout-upgrade.md`
  - `docs/branch-intents/2026-04-22-tighten-ui-filters-and-metadata.md`
  - `docs/branch-intents/2026-04-22-ui-componentization-rules.md`
- Relevant lessons pulled forward:
  - Keep changes additive and API-compatible.
  - Validate with targeted frontend build checks.
- Rabbit holes to avoid this time:
  - Large backend redesign for UI-only asks.
  - Building a full map/settings persistence story.

## Architecture decisions
- Decision:
  - Keep the existing browse layout but improve interaction density and control placement rather than re-architecting pages.
- Why:
  - This directly addresses UX pain points in one incremental pass with low risk.
- Tradeoff:
  - Some “dead code” remains outside the touched flow (e.g., map placeholder component file) to avoid a broad cleanup unrelated to runtime behavior.

## Error log (mandatory)
- Exact error message(s):
  - `src/ui/components/SettingsView.tsx(1,15): error TS2305: Module '"../types"' has no exported member 'SettingsState'.`
- Where seen (command/log/file):
  - `npm run -w services/app/client build`
- Frequency or reproducibility notes:
  - Reproducible after removing `SettingsState` from shared types while `SettingsView.tsx` still existed.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Updated browse UI components for collapsible filters, sticky detail pane, compact cards, quick hover actions, and sort control relocation.
  - Why this was tried:
    - Matches direct user feedback about pane behavior, button density, and controls placement.
  - Result:
    - Successful for behavior, but introduced a TypeScript build break from stale settings component typing.
- Attempt 2:
  - Change made:
    - Removed the unused settings view component/style and re-ran builds.
  - Why this was tried:
    - User requested removing settings surface and dead UI code.
  - Result:
    - Successful; frontend and server builds pass.

## What went right (mandatory)
- The browse surface now reflects the requested interaction tweaks without changing API shape beyond optional max print-score filtering.
- Targeted build validation passed after cleanup.

## What went wrong (mandatory)
- Initial type removal left a stale component referencing deleted types, causing a client build error before cleanup.

## Validation (mandatory)
- Commands run:
  - `npm run -w services/app/client build`
  - `npm run -w services/app/server build`
- Observed results:
  - Both commands completed successfully after the settings component cleanup.

## Follow-up
- Next branch goals:
  - Add stronger visual active-state treatment for quick card actions (favorite/keep/reject) and optional tooltips.
- What to try next if unresolved:
  - If users want persistent filter-pane collapsed state, store it in localStorage.
