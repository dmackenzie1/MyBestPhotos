# Branch Intent: 2026-04-22-audit-nima-usage-question

## Intent
- Verify whether this repository currently uses NIMA-based (or NIMA-style) photo assessment and provide a source-backed answer.

## Scope
- In scope:
  - Audit code/docs for `nima` and related advanced scoring entry points.
  - Confirm whether implementation is a true Neural Image Assessment model or a heuristic proxy.
  - Record findings for future contributors.
- Out of scope:
  - Implementing or integrating a new trained NIMA model.
  - Changing scoring behavior.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-two-stage-ingest-advanced-nima.md`
  - `docs/branch-intents/2026-04-22-audit-ingest-browse-search-scoring.md`
- Relevant lessons pulled forward:
  - Keep changes minimal and additive.
  - Prefer explicit documentation for what is model-backed vs heuristic.
- Rabbit holes to avoid this time:
  - Avoid broad pipeline refactors when the task is verification-only.

## Architecture decisions
- Decision:
  - Add a lightweight branch-intent audit entry only; do not alter runtime code.
- Why:
  - User asked for current-state verification, not a feature change.
- Tradeoff:
  - No functional improvement in this branch; value is traceability and clarity.

## Error log (mandatory)
- Exact error message(s):
  - No runtime error encountered.
  - User-facing uncertainty captured as: "are we using the NIMA: Neural IMage Assessment to assess photos? I dont see reference to this in the project yet"
- Where seen (command/log/file):
  - User request in task conversation.
- Frequency or reproducibility notes:
  - Reproducible as a documentation/discoverability question rather than a code exception.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Searched repository for NIMA/aesthetic scoring references via `rg`.
  - Why this was tried:
    - Fastest way to validate whether NIMA paths exist in code/docs.
  - Result:
    - Successful; found CLI command (`score-nima`), advanced-stage logic, and docs references.
- Attempt 2:
  - Change made:
    - Reviewed prior branch intent documenting initial NIMA-style rollout.
  - Why this was tried:
    - Confirm whether implementation is true model inference vs heuristic proxy.
  - Result:
    - Successful; confirmed current implementation is explicitly `nima_style_v0` heuristic.

## What went right (mandatory)
- NIMA-related implementation and docs were easy to locate with targeted search.

## What went wrong (mandatory)
- Discoverability gap for readers scanning only top-level code paths remains possible.

## Validation (mandatory)
- Commands run:
  - `rg -n "nima|aesthetic|keep_score|score-nima|nima_style" src tests docs README*`
  - `cat docs/branch-intents/2026-04-22-two-stage-ingest-advanced-nima.md`
- Observed results:
  - Confirmed active NIMA-style scoring flow in CLI + pipeline docs/code.
  - Confirmed current scorer is a deterministic proxy, not a full trained NIMA model.

## Follow-up
- Next branch goals:
  - Improve top-level documentation callout so users can quickly find NIMA-style pipeline entry points.
- What to try next if unresolved:
  - Add a dedicated README section comparing legacy `aesthetics.py` and `pipeline_v1` advanced scoring.
