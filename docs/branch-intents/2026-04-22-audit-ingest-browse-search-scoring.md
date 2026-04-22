# Branch Intent: 2026-04-22-audit-ingest-browse-search-scoring

## Intent
- Audit ingest, browse, search, filters, placeholders, and scoring implementation; close remaining gaps with low-risk fixes.

## Scope
- In scope:
  - Verify existing implementations for ingest limits, pagination/load-more, search reset behavior, filters, timeline/map placeholders, and scoring.
  - Add missing ingest env compatibility and selection strategy support.
  - Improve deterministic scoring inputs for filter/discovery usefulness.
  - Update docs/examples for new env behavior.
- Out of scope:
  - ORM refactor.
  - Full timeline/map feature implementation.
  - Large schema changes.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-planning-ingest-browse-cleanups.md`
  - `docs/branch-intents/2026-04-22-validate-external-code-review.md`
  - `docs/branch-intents/2026-04-22-ingest-consistency-and-db-lifecycle.md`
- Relevant lessons pulled forward:
  - Keep behavior changes incremental and directly testable.
  - Avoid schema-wide rewiring for targeted UX/pipeline improvements.
- Rabbit holes to avoid this time:
  - Reworking table model boundaries (`photos` vs `files`) in one branch.

## Architecture decisions
- Decision:
  - Keep current SQL/table-definition-first architecture and apply additive improvements only.
- Why:
  - Most requested capabilities already exist; targeted fixes are lower risk and faster to verify.
- Tradeoff:
  - Some technical debt remains (mixed legacy/new pipeline modules), but no new instability introduced.

## Error log (mandatory)
- Exact error message(s):
  - `Failed to download nvidia-nccl-cu13==2.28.9`
  - `tunnel error: unsuccessful`
- Where seen (command/log/file):
  - During `uv run --project . ruff format ...` / `uv run --project . ruff check ...` dependency resolution in this environment.
- Frequency or reproducibility notes:
  - Reproducible in this session due network/proxy policy on Python wheel download.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Audited current server/client/pipeline codepaths and confirmed existing pagination, filters, and placeholders are already implemented.
  - Why this was tried:
    - Required by task: verify before re-implementing.
  - Result:
    - Successful; only targeted gaps remained.
- Attempt 2:
  - Change made:
    - Added ingest env compatibility aliases and extended selection strategy support (`newest`) in settings + discovery selection.
  - Why this was tried:
    - Align behavior with requested env contract (`INGEST_FILE_LIMIT`, strategy support including newest) without breaking existing `PHOTO_CURATOR_*` vars.
  - Result:
    - Successful.
- Attempt 3:
  - Change made:
    - Added deterministic category extraction from description text and fed categories into semantic scoring.
  - Why this was tried:
    - Improve practical scoring/discovery quality and make topic filters useful in non-LM datasets.
  - Result:
    - Successful.
- Attempt 4:
  - Change made:
    - Added/updated tests for `newest` ingest selection and ingest env alias loading behavior.
  - Why this was tried:
    - Verify new logic and prevent regressions.
  - Result:
    - Successful with local Python test execution fallback.

## What went right (mandatory)
- Existing browse/filter/pagination/timeline-map groundwork was already present and stable.
- New ingest and scoring improvements were additive and isolated.

## What went wrong (mandatory)
- `uv run` validation path failed due external wheel download constraints, requiring fallback to locally available tooling for checks.

## Validation (mandatory)
- Commands run:
  - `uv run --project . ruff format src/photo_curator/config.py src/photo_curator/pipeline_v1.py tests/test_ingest_selection.py tests/test_config_ingest_env_aliases.py`
  - `python -m pip show ruff >/dev/null 2>&1 && ruff format src/photo_curator/config.py src/photo_curator/pipeline_v1.py tests/test_ingest_selection.py tests/test_config_ingest_env_aliases.py && ruff check src/photo_curator/config.py src/photo_curator/pipeline_v1.py tests/test_ingest_selection.py tests/test_config_ingest_env_aliases.py || true; PYTHONPATH=src python -m unittest tests/test_ingest_selection.py tests/test_config_ingest_env_aliases.py`
  - `npm run -w services/app/server build && npm run -w services/app/client build`
- Observed results:
  - `uv run` failed in this environment due dependency fetch/network tunneling error.
  - Ruff + Python unit tests passed via local interpreter path.
  - Server/client TypeScript builds passed.

## Follow-up
- Next branch goals:
  - Add API-level tests for composed filters (`q` + date + camera + category + score + status) with pagination.
  - Consider a `newest` option surfacing in user-facing docs/UI controls if needed.
- What to try next if unresolved:
  - If large dataset listing performance degrades, add keyset pagination and indexes for dominant sort/filter paths.
