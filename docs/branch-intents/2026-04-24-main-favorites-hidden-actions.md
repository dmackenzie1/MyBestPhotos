# Branch Intent: 2026-04-24-main-favorites-hidden-actions

## Quick Summary
- Purpose: Simplify browse labeling UX so users work with Main, Favorites, and Hidden only; remove print-size and keep/reject surface from UI; avoid list reload feel when action buttons are pressed.
- Keywords: main, favorites, hidden, actions
## Intent
- Simplify browse labeling UX so users work with Main, Favorites, and Hidden only; remove print-size and keep/reject surface from UI; avoid list reload feel when action buttons are pressed.

## Scope
- In scope:
  - React client updates for status tabs/filters and action button behavior in browse/detail panes.
  - API status query support for `hidden` and ensuring `all`/`favorite` exclude hidden photos.
  - Branch-intent documentation for this task.
- Out of scope:
  - Database schema migration/removal of legacy columns in this pass.
  - Scoring model logic changes.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-24-ui-browse-pane-iteration.md`
  - `docs/branch-intents/2026-04-24-ui-timeline-filters-modernization.md`
  - `docs/branch-intents/2026-04-24-remove-filename-sort-option.md`
- Relevant lessons pulled forward:
  - Keep UX changes incremental and API-compatible where possible.
  - Validate with targeted client/server build commands.
- Rabbit holes to avoid this time:
  - Broad schema cleanup while UX behavior can be fixed in existing label fields.

## Architecture decisions
- Decision:
  - Reuse existing `reject_flag` as the hidden state and add a `hidden` query status alias.
  - Replace full list/detail refetch after label patch with local state patching.
- Why:
  - Delivers the requested UX quickly without schema churn and removes perceived full-page refresh behavior.
- Tradeoff:
  - Legacy `keep`/print-related data remains in API/schema for backward compatibility until a dedicated cleanup migration.

## Error log (mandatory)
- Exact error message(s):
  - None encountered during implementation.
- Where seen (command/log/file):
  - N/A.
- Frequency or reproducibility notes:
  - N/A.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Updated UI status options/tabs to Main/Favorites/Hidden, removed keep/reject labels and print-size action buttons, and made buttons explicit `type="button"`.
  - Why this was tried:
    - Match requested simplified panel model and eliminate accidental form-submit-like refresh behavior.
  - Result:
    - Successful.
- Attempt 2:
  - Change made:
    - Updated label patch flow to mutate local list/detail state after PATCH instead of re-fetching list/detail on each click.
  - Why this was tried:
    - Remove jarring reload behavior and make button interactions feel instant.
  - Result:
    - Successful.

## What went right (mandatory)
- The patch stayed localized to client UX and a small server filter adjustment while preserving API compatibility.

## What went wrong (mandatory)
- No major implementation issues; database-level cleanup remains for a future focused migration task.

## Validation (mandatory)
- Commands run:
  - `npm run -w services/app/client build`
  - `npm run -w services/app/server build`
- Observed results:
  - Both builds passed.

## Follow-up
- Next branch goals:
  - Remove deprecated keep/print flags and score columns from schema/API once migration strategy is approved.
- What to try next if unresolved:
  - If hidden/favorite semantics need to overlap differently, codify precedence in API contract and update `statusFromItem` accordingly.
