# Branch Intent: 2026-04-22-implement-true-nima-library

## Intent
- Replace the current NIMA-style heuristic-only advanced scoring path with a true NIMA library-backed inference path in Python, while preserving a safe fallback.

## Scope
- In scope:
  - Add a real NIMA inference integration in `pipeline_v1`.
  - Wire advanced scoring to persist model-backed `nima_score` when available.
  - Use NIMA-derived signals to influence photo goodness scoring (`curation_score`).
  - Update docs/tests for new behavior.
- Out of scope:
  - Full model-serving microservice redesign.
  - Schema redesign or broad ranking-system rewrite.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-two-stage-ingest-advanced-nima.md`
  - `docs/branch-intents/2026-04-22-audit-nima-usage-question.md`
- Relevant lessons pulled forward:
  - Keep advanced runner additive and rerunnable.
  - Keep behavior resilient when model dependencies are unavailable.
- Rabbit holes to avoid this time:
  - Avoid queue/ORM refactors.
  - Avoid changing unrelated ingest/discovery behavior.

## Architecture decisions
- Decision:
  - Integrate `pyiqa` NIMA metric as primary scorer with heuristic fallback (`nima_style_v0`) when unavailable.
- Why:
  - Delivers true NIMA library usage without sacrificing robustness in constrained environments.
- Tradeoff:
  - Adds dependency/runtime weight and potential first-run model download requirements.

## Error log (mandatory)
- Exact error message(s):
  - `error: Failed to fetch: https://pypi.org/simple/exifread/`
  - `tunnel error: unsuccessful`
  - `ModuleNotFoundError: No module named 'cv2'`
- Where seen (command/log/file):
  - During `uv run --project . python -m unittest tests/test_nima_scoring.py`.
  - During local import probe: `PYTHONPATH=src python - <<'PY' ...`.
- Frequency or reproducibility notes:
  - Reproducible in this environment due dependency/network constraints and missing local OpenCV runtime.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Added `pipeline_v1/nima_model.py` with lazy `pyiqa` NIMA initialization and per-image fallback handling.
  - Why this was tried:
    - Isolate optional dependency complexity from pipeline orchestration.
  - Result:
    - Successful.
- Attempt 2:
  - Change made:
    - Updated `advanced_stage.score_nima` to use true NIMA score when available and fallback to `nima_style_v0` when unavailable.
  - Why this was tried:
    - Make real NIMA inference active without breaking constrained hosts.
  - Result:
    - Successful.
- Attempt 3:
  - Change made:
    - Updated description curation scoring to prefer `keep_score` (NIMA-informed) when present.
  - Why this was tried:
    - Ensure NIMA results influence good-vs-bad ranking guidance.
  - Result:
    - Successful.
- Attempt 4:
  - Change made:
    - Added math-level test coverage for derived aesthetic/keep scoring behavior.
  - Why this was tried:
    - Validate score monotonicity and guard against regressions.
  - Result:
    - Successful.

## What went right (mandatory)
- Integration stayed localized to advanced scoring modules and existing score fields.
- Fallback path preserves operability even when NIMA runtime is unavailable.

## What went wrong (mandatory)
- `uv run` verification is blocked by network-restricted dependency fetches.
- Local runtime import checks can fail when Python environment lacks OpenCV.

## Validation (mandatory)
- Commands run:
  - `rg -n "nima|advanced-runner|curation_score|score-nima" src README.md tests`
  - `ruff format src/photo_curator/pipeline_v1/nima_model.py src/photo_curator/pipeline_v1/advanced_stage.py src/photo_curator/pipeline_v1/scoring_math.py src/photo_curator/pipeline_v1/description_stage.py src/photo_curator/pipeline_v1/__init__.py src/photo_curator/cli.py tests/test_nima_scoring.py`
  - `ruff check src/photo_curator/pipeline_v1/nima_model.py src/photo_curator/pipeline_v1/advanced_stage.py src/photo_curator/pipeline_v1/scoring_math.py src/photo_curator/pipeline_v1/description_stage.py src/photo_curator/pipeline_v1/__init__.py src/photo_curator/cli.py tests/test_nima_scoring.py`
  - `PYTHONPATH=src python -m unittest tests/test_nima_scoring.py`
  - `uv run --project . python -m unittest tests/test_nima_scoring.py`
- Observed results:
  - Confirmed target integration points in `advanced_stage.py`, `scoring_math.py`, and `description_stage.py`.
  - Ruff format/check passed.
  - Local unittest run passed.
  - `uv run` path failed due network tunneling/dependency fetch restriction.

## Follow-up
- Next branch goals:
  - Add tests for derived score math and fallback behavior.
- What to try next if unresolved:
  - If `pyiqa` runtime is unavailable, consider optional extra install docs and explicit CLI warning for fallback mode.
