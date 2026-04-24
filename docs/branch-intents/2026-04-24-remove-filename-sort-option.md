# Branch Intent: 2026-04-24-remove-filename-sort-option

## Intent
- Remove the filename sort option from the browse UI sort dropdown so users only see ranking/time-oriented sorts.

## Scope
- In scope:
  - Update the React browse grid sort options in `services/app/client/src/ui/components/PhotoGrid.tsx`.
  - Record this task’s attempt/results in a branch-intent document.
- Out of scope:
  - Backend API sort enum/query behavior changes.
  - Any scoring formula changes.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-24-ui-browse-pane-iteration.md`
- Relevant lessons pulled forward:
  - Keep the patch focused on the UI when the request is strictly presentation/UX.
  - Re-run targeted frontend build validation after UI edits.
- Rabbit holes to avoid this time:
  - Unnecessary server/API refactors for a dropdown-option removal.

## Architecture decisions
- Decision:
  - Remove only the `filename_asc` entry from the client `SORT_OPTIONS` list.
- Why:
  - User request is to remove that option from what they can select in the app UI.
- Tradeoff:
  - API still accepts `filename_asc` for direct query callers/bookmarks, which preserves backward compatibility but leaves hidden capability.

## Error log (mandatory)
- Exact error message(s):
  - None encountered.
- Where seen (command/log/file):
  - N/A.
- Frequency or reproducibility notes:
  - N/A.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Removed `{ value: "filename_asc", label: "Filename" }` from browse sort options.
  - Why this was tried:
    - Directly satisfies user ask to get rid of filename sort from the UI.
  - Result:
    - Successful; option no longer appears in the dropdown.

## What went right (mandatory)
- Change was low-risk, single-file UI edit aligned with existing structure.
- Frontend build validation succeeded after the change.

## What went wrong (mandatory)
- Nothing significant; no errors encountered.

## Validation (mandatory)
- Commands run:
  - `npm run -w services/app/client build`
- Observed results:
  - Command completed successfully.

## Follow-up
- Next branch goals:
  - If desired, remove `filename_asc` from server query enum too after confirming no API clients rely on it.
- What to try next if unresolved:
  - If users still reach filename sorting via URL params, reject/deprecate `filename_asc` at API level and return a validation error.
