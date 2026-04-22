# Branch Intent: 2026-04-22-fix-review-actionable-items

## Intent
- Implement a focused subset of actionable fixes from the external review that are low-risk and directly verifiable.

## Scope
- In scope:
  - Fix Docker fallback DB hostname mismatch in app-server.
  - Simplify file iteration API in `pipeline_v1` and avoid eager list materialization.
  - Remove dead HEIC/HEIF skip condition in `ingest.py`.
  - Clarify fallback embedding naming in `embeddings.py`.
  - Add inline config note explaining `default_roots` env parsing strategy.
- Out of scope:
  - Full legacy/new schema unification.
  - Query-builder migration for SQL statements.
  - ANN/vector-index redesign.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-validate-external-code-review.md`
  - `docs/branch-intents/2026-04-22-ingest-consistency-and-db-lifecycle.md`
  - `docs/branch-intents/2026-04-22-fix-default-roots-env-jsondecode.md`
- Relevant lessons pulled forward:
  - Keep changes incremental and avoid schema-wide refactors in one patch.
  - Prefer changes that are easy to validate via static checks in this environment.
- Rabbit holes to avoid this time:
  - Attempting to migrate all legacy `photos/*` consumers to `files/*`.

## Architecture decisions
- Decision:
  - Keep behavior stable while improving correctness/readability in small targeted places.
- Why:
  - User asked to “fix the ones we can,” which favors practical, low-risk cleanups.
- Tradeoff:
  - Some deeper issues remain and are documented for follow-up.

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
    - Planned and applied small targeted edits in server + Python pipeline modules.
  - Why this was tried:
    - Maximize value while minimizing regression risk.
  - Result:
    - Successful.
- Attempt 2:
  - Change made:
    - Ran Python formatting/lint checks on touched files.
  - Why this was tried:
    - Ensure style and static quality before commit.
  - Result:
    - Successful.

## What went right (mandatory)
- All selected fixes were local and straightforward to verify.

## What went wrong (mandatory)
- Full integration/runtime validation remains limited by environment constraints.

## Validation (mandatory)
- Commands run:
  - `ruff format src/photo_curator/config.py src/photo_curator/pipeline_v1.py src/photo_curator/ingest.py src/photo_curator/embeddings.py`
  - `ruff check src/photo_curator/config.py src/photo_curator/pipeline_v1.py src/photo_curator/ingest.py src/photo_curator/embeddings.py`
  - `npm run -w services/app/server build`
- Observed results:
  - Commands completed successfully in this environment.

## Follow-up
- Next branch goals:
  - Evaluate batching/transaction changes for metric/description writes.
  - Plan legacy-to-v1 schema convergence path.
- What to try next if unresolved:
  - Introduce a compatibility layer or phased migration strategy for legacy modules.
