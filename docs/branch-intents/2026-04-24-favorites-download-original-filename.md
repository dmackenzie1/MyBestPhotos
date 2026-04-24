# Branch Intent: 2026-04-24-favorites-download-original-filename

## Intent
- Add an explicit per-photo download action (especially useful in Favorites) that downloads the original image using the original filename.

## Scope
- In scope:
  - Client action buttons for card/detail photo downloads.
  - Server image endpoint behavior for forcing file download when requested.
- Out of scope:
  - Bulk download workflows.
  - Any metadata/schema changes.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-24-main-favorites-hidden-actions.md`
  - `docs/branch-intents/2026-04-24-ui-browse-pane-iteration.md`
- Relevant lessons pulled forward:
  - Keep UI changes incremental and avoid broad refactors.
  - Prefer API-compatible additions over changing existing behavior.
- Rabbit holes to avoid this time:
  - Avoiding a full download manager/batch feature when the request is per-image.

## Architecture decisions
- Decision:
  - Add a dedicated download icon/button in card actions and a Download link in the detail pane.
  - Introduce `download=1` query support on `GET /api/v1/photos/:id/image` to switch `Content-Disposition` to `attachment`.
- Why:
  - This gives a one-click per-image download path and reliably preserves the filename via `downloadName`.
- Tradeoff:
  - Endpoint behavior gains a small query-param branch, but defaults remain unchanged (`inline`) for existing callers.

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
    - Added a fourth action on grid cards using a download icon (`⤓`) that hits the image endpoint with `download=1` and `downloadName=<original filename>`.
  - Why this was tried:
    - Matches the requested UX (star, hide/show, expand, download).
  - Result:
    - Successful.
- Attempt 2:
  - Change made:
    - Updated server image route to honor `download=1|true` with `Content-Disposition: attachment; filename=...`.
  - Why this was tried:
    - Makes download behavior explicit and consistent across browsers.
  - Result:
    - Successful.

## What went right (mandatory)
- The change stayed minimal and reused the existing `downloadName` parameter to preserve original filenames.

## What went wrong (mandatory)
- No major issues; did not validate in-browser screenshot due unavailable browser container tool in this run context.

## Validation (mandatory)
- Commands run:
  - `npm run -w services/app/client build`
  - `npm run -w services/app/server build`
- Observed results:
  - Both builds passed.

## Follow-up
- Next branch goals:
  - Consider adding tooltips or text labels for action icons for stronger discoverability/accessibility.
- What to try next if unresolved:
  - If any browser still opens instead of downloading, add RFC 5987 `filename*=` fallback in Content-Disposition.
