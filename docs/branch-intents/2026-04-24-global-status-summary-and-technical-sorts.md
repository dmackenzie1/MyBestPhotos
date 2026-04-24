# Branch Intent: 2026-04-24-global-status-summary-and-technical-sorts

## Intent
- Make Favorites/Hidden counts global (not tied to currently loaded page), add technical sort options, and tighten right-pane/readability + suggested topic chips in the browse UI.

## Scope
- In scope:
  - Add a status-summary API query for global Main/Favorites/Hidden/Unreviewed counts under active non-status filters.
  - Wire client to fetch/use global counts and refresh after label actions.
  - Add sort options for sharpness/exposure/contrast/noise in browse/timeline sort dropdowns.
  - UI polish for detail source-path readability and suggested topic chips.
- Out of scope:
  - New DB schema migrations or metric computation changes.
  - Major layout redesign beyond requested spacing/font tweaks.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-24-main-favorites-hidden-actions.md`
  - `docs/branch-intents/2026-04-24-ui-browse-pane-iteration.md`
  - `docs/branch-intents/2026-04-24-remove-filename-sort-option.md`
- Relevant lessons pulled forward:
  - Keep changes additive and API-compatible.
  - Validate with targeted client/server build commands.
  - Avoid broad schema cleanup in UX-driven changes.
- Rabbit holes to avoid this time:
  - Reworking scoring pipelines when sort can be done with existing metric columns.

## Architecture decisions
- Decision:
  - Add `/api/v1/photos/status-summary` using the same filter surface (minus status/paging/sort) and SQL `COUNT(*) FILTER` aggregations.
- Why:
  - Produces global tab counts consistent with the current filter context without requiring infinite-scroll completion.
- Tradeoff:
  - Adds one lightweight API call per filter change and post-label update.

## Error log (mandatory)
- Exact error message(s):
  - None encountered so far.
- Where seen (command/log/file):
  - N/A.
- Frequency or reproducibility notes:
  - N/A.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Added server summary endpoint and technical sort enum/order mappings.
  - Why this was tried:
    - Needed backend support for global status counts and new UI sort choices.
  - Result:
    - Successful.
- Attempt 2:
  - Change made:
    - Updated client to request summary counts, refresh after label patch, and expanded sort/topic/detail-pane UI.
  - Why this was tried:
    - Match direct user requests for counts visibility, sort controls, and right-pane/topic improvements.
  - Result:
    - Successful.

## What went right (mandatory)
- Changes stayed scoped to existing browse API/client structures and reused current filter semantics.

## What went wrong (mandatory)
- Minor duplicate condition insertion in `scoreBadgeForSort` occurred during first edit pass and was corrected before validation.

## Validation (mandatory)
- Commands run:
  - `npm run -w services/app/client build`
  - `npm run -w services/app/server build`
- Observed results:
  - Both builds passed; npm emitted a non-fatal `Unknown env config "http-proxy"` warning.

## Follow-up
- Next branch goals:
  - Optionally add dedicated metric badges for technical sorts once list API includes those metric fields.
- What to try next if unresolved:
  - If summary query load becomes noticeable, return summary alongside list response via optional include flag.
