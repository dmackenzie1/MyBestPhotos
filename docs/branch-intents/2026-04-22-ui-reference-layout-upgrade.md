# Branch Intent: 2026-04-22-ui-reference-layout-upgrade

## Intent
- Move the client UI closer to the provided photo-management reference by strengthening browse ergonomics (details pane richness, filter affordances, timeline mode, settings mode, and endless scrolling behavior).

## Scope
- In scope:
  - React client layout and interaction updates in `services/app/client/src/App.tsx`.
  - UI styling updates in `services/app/client/src/styles.css`.
  - Branch-intent record for this task.
- Out of scope:
  - Backend API shape changes.
  - Geospatial map implementation.
  - Authentication/profile/settings persistence in backend storage.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-ui-screenshot-tooling.md`
  - `docs/branch-intents/2026-04-22-fix-review-actionable-items.md`
- Relevant lessons pulled forward:
  - Keep changes additive and low-drama while improving usability.
  - Prefer verifiable, scoped edits and run targeted checks for touched frontend code.
- Rabbit holes to avoid this time:
  - Large backend schema/API migrations to support UI ideas in one pass.
  - Attempting full map feature parity before metadata coverage is ready.

## Architecture decisions
- Decision:
  - Reuse existing API contract and extend client-only state/presentation to provide reference-like structure.
- Why:
  - The fastest path to visible UX progress without destabilizing services is to improve layout, controls, and browse flow using already available fields.
- Tradeoff:
  - Some reference capabilities are represented as placeholders or session-only preferences until backend support is added.

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
    - Added browse status tabs, topic chips, detail metadata/tags, timeline grouping view, and settings toggles.
  - Why this was tried:
    - These are the strongest visual/interaction matches to the reference and mostly client-side.
  - Result:
    - Successful.
- Attempt 2:
  - Change made:
    - Replaced manual pagination button flow with an intersection-observer sentinel for endless scrolling UX.
  - Why this was tried:
    - The reference explicitly emphasizes continuous scrolling behavior.
  - Result:
    - Successful.

## What went right (mandatory)
- The update remained API-compatible and concentrated in two frontend files.
- Timeline and settings became first-class views instead of generic placeholders.

## What went wrong (mandatory)
- Full map and persistent settings are not yet implemented; these remain future follow-up items.

## Validation (mandatory)
- Commands run:
  - `npm run -w services/app/client build`
- Observed results:
  - Build completed successfully.

## Follow-up
- Next branch goals:
  - Add date histogram and richer facet controls.
  - Persist settings preferences and wire map view when GPS confidence is available.
- What to try next if unresolved:
  - Add lightweight client preference storage and request backend facet expansions for timeline buckets.
