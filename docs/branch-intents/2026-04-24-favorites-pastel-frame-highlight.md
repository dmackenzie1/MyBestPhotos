# Branch Intent: 2026-04-24-favorites-pastel-frame-highlight

## Quick Summary
- Branch: `2026-04-24-favorites-pastel-frame-highlight`
- Purpose: Add a subtle, muted highlight border around favorite photo cards so favorites are easier to spot without introducing bright/glowing colors.
- Scan first: Use this branch when you are working on the same feature area or error pattern.



## Intent
- Add a subtle, muted highlight border around favorite photo cards so favorites are easier to spot without introducing bright/glowing colors.

## Scope
- In scope:
  - Frontend card class/state wiring for favorite items.
  - Frontend CSS styling for a pastel/muted favorite border accent.
  - Branch-intent documentation for this UI tweak.
- Out of scope:
  - Backend/API behavior changes.
  - Changes to non-favorite card color systems.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-24-main-favorites-hidden-actions.md`
  - `docs/branch-intents/2026-04-24-ui-condensed-browse-cleanup.md`
  - `docs/branch-intents/2026-04-24-ui-browse-pane-iteration.md`
- Relevant lessons pulled forward:
  - Keep UI edits incremental and localized to client files.
  - Preserve existing interaction behavior and run targeted client build validation.
- Rabbit holes to avoid this time:
  - Any backend/schema refactor for a purely visual request.

## Architecture decisions
- Decision:
  - Attach a conditional `favorite-frame` class on card articles when `favoriteFlag` is true and style it with a subdued pastel-yellow border + soft inset line.
- Why:
  - This delivers the requested “little highlight around the border” while staying understated and consistent with the dark theme.
- Tradeoff:
  - Only favorites receive this accent; non-favorite cards remain unchanged, so emphasis relies on favorite labeling state.

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
    - Added conditional `favorite-frame` class to card markup when `item.favoriteFlag` is true.
  - Why this was tried:
    - Needed a simple state hook for styling favorite cards only.
  - Result:
    - Successful.
- Attempt 2:
  - Change made:
    - Added muted pastel-yellow border and soft inset highlight in card CSS.
  - Why this was tried:
    - Match user ask for minor, muted/pastel framing effect instead of bright glow.
  - Result:
    - Successful.

## What went right (mandatory)
- The tweak is isolated to existing card render/styling and keeps all interactions intact.

## What went wrong (mandatory)
- Browser screenshot tooling is unavailable in this environment, so visual artifact capture could not be produced.

## Validation (mandatory)
- Commands run:
  - `npm run -w services/app/client build`
- Observed results:
  - Client build completed successfully.

## Follow-up
- Next branch goals:
  - Optionally tune favorite frame tone/intensity via CSS custom property for easy theme adjustment.
- What to try next if unresolved:
  - If users want stronger separation, add a slightly warmer top-edge gradient while keeping muted saturation.
