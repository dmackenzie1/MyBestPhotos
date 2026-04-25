# Branch Intent: 2026-04-24-llm-photo-descriptions-and-semantic-search

## Quick Summary
- Purpose: Add an LM Studio-backed LLM processing pass that generates per-photo descriptions/tags/scores and semantic-search vectors, then expose these results in API/UI search flows.
- Keywords: llm, photo, descriptions, and, semantic, search
## Intent
- Add an LM Studio-backed LLM processing pass that generates per-photo descriptions/tags/scores and semantic-search vectors, then expose these results in API/UI search flows.

## Scope
- In scope:
  - Add Postgres schema for LLM runs and per-file LLM results (one current row per file).
  - Add Python LLM runner stage + CLI command for full-pass processing.
  - Add local CPU-friendly tokenizer/embedding generation for semantic vectors.
  - Add API-side hybrid search (keyword + vector) and surface LLM fields in responses.
  - Add compose/env/docs wiring for LLM runner defaults.
- Out of scope:
  - Multi-version history UX (beyond storing last-run linkage metadata).
  - GPU-specific optimization and batching heuristics.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-24-full-pass-deferred-advanced-rescore.md`
  - `docs/branch-intents/2026-04-24-global-status-summary-and-technical-sorts.md`
  - `docs/branch-intents/2026-04-22-update-lmstudio-default-model-qwen3.6-35b-a3b.md`
- Relevant lessons pulled forward:
  - Keep changes additive and compatible with existing list/detail APIs.
  - Prefer full-pass runners with explicit CLI/config knobs.
  - Keep startup/compose docs synchronized with behavior changes.
- Rabbit holes to avoid this time:
  - Full architecture rewrite of scoring pipelines.
  - Overly complex job orchestration when one-shot runner aligns with current pattern.

## Architecture decisions
- Decision:
  - Introduce `llm_runs` and `file_llm_results` tables (1:1 active file row) and hybrid search ranking in API.
- Why:
  - Keeps current behavior simple while preserving run metadata (`prompt_version`, model, timestamps) and supporting semantic retrieval.
- Tradeoff:
  - Historical per-file result versions are not persisted yet; only latest per file is retained.

## Error log (mandatory)
- Exact error message(s):
  - `error: Failed to spawn: `pre-commit``
  - `Caused by: No such file or directory (os error 2)`
- Where seen (command/log/file):
  - `uv run pre-commit run --all-files`
- Frequency or reproducibility notes:
  - Reproducible in this environment; pre-commit executable is not installed.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Added schema extensions (`llm_runs`, `file_llm_results` + pgvector/text indexes) in both init and bootstrap SQL.
  - Why this was tried:
    - Needed one-to-one per-photo LLM result storage and vector search persistence.
  - Result:
    - Successful.
- Attempt 2:
  - Change made:
    - Added Python `llm-runner` stage/CLI using LM Studio chat completions with strict JSON output, plus deterministic CPU tokenizer embeddings.
  - Why this was tried:
    - Implement full-pass generation of descriptions/tags/scores/vectors with configurable endpoint+model.
  - Result:
    - Successful.
- Attempt 3:
  - Change made:
    - Added API/server hybrid search plumbing and UI/detail field surfacing (`wallArtScore`) with shared contract updates.
  - Why this was tried:
    - Expose LLM output in browse/detail and use query text for vector-aware retrieval.
  - Result:
    - Successful.

## What went right (mandatory)
- End-to-end path now exists from LLM generation to persisted vectors to API/UI visibility with additive schema changes.
- Config/compose defaults now target localhost LM Studio and include a dedicated one-shot LLM runner service.

## What went wrong (mandatory)
- Pre-commit aggregate validation path is unavailable in this runtime due missing binary.

## Validation (mandatory)
- Commands run:
  - `python -m compileall src/photo_curator`
  - `uv run --project . ruff check src/photo_curator/pipeline_v1/llm_stage.py src/photo_curator/text_vectorizer.py src/photo_curator/cli.py src/photo_curator/pipeline_v1/models.py src/photo_curator/config.py`
  - `uv run --project . ruff format src/photo_curator/pipeline_v1/llm_stage.py src/photo_curator/text_vectorizer.py src/photo_curator/cli.py src/photo_curator/pipeline_v1/models.py src/photo_curator/config.py`
  - `npm run -w packages/shared build`
  - `npm run -w services/app/server build`
  - `npm run -w services/app/client build`
  - `uv run pre-commit run --all-files`
- Observed results:
  - Python compile succeeded.
  - Ruff check/format succeeded.
  - Shared/server/client TypeScript builds succeeded.
  - pre-commit command failed due missing executable in this environment.

## Follow-up
- Next branch goals:
  - Iterate prompt quality, add optional historical version tables, and tune rank blending weights.
- What to try next if unresolved:
  - Add endpoint-level explain diagnostics for hybrid rank score components.
