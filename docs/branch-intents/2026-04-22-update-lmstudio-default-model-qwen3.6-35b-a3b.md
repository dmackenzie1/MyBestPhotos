# Branch Intent: 2026-04-22-update-lmstudio-default-model-qwen3.6-35b-a3b

## Quick Summary
- Purpose: Align repository defaults and documentation with the user’s LM Studio model (`qwen3.6-35b-a3b`) so setup and runtime behavior match out of the box.
- Keywords: update, lmstudio, default, model, qwen3.6, 35b, a3b
## Intent
- Align repository defaults and documentation with the user’s LM Studio model (`qwen3.6-35b-a3b`) so setup and runtime behavior match out of the box.

## Scope
- In scope:
  - Update LM Studio default model value in environment examples, compose defaults, and Python settings defaults.
  - Update README examples that currently reference the prior model.
- Out of scope:
  - Changing provider behavior or adding new LM Studio-specific flags.
  - Updating non-default model-name concepts unrelated to LM Studio defaults.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-ingest-consistency-and-db-lifecycle.md`
  - `docs/branch-intents/2026-04-22-single-photo-ingest-root-env.md`
- Relevant lessons pulled forward:
  - Keep patch incremental and focused to config/docs consistency.
  - Validate touched files with targeted commands.
- Rabbit holes to avoid this time:
  - Avoid broader refactors in ingest/pipeline code not required for default-model alignment.

## Architecture decisions
- Decision:
  - Keep existing LM Studio integration and only change default model strings from `qwen2.5-vl-7b-instruct` to `qwen3.6-35b-a3b`.
- Why:
  - User explicitly requested updating defaults in `.env`, README, and all other matching defaults.
- Tradeoff:
  - New default may be heavier for low-resource systems; users can still override via env/CLI.

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
    - Replaced old LM Studio model default string in `.env.example`, `docker-compose.yml`, `src/photo_curator/config.py`, `src/photo_curator/pipeline_v1.py`, and README command examples.
  - Why this was tried:
    - Ensure user-facing docs and runtime defaults are fully consistent.
  - Result:
    - Successful; all known references now point to `qwen3.6-35b-a3b`.

## What went right (mandatory)
- All direct default references to the prior model were found and updated in one pass.

## What went wrong (mandatory)
- No functional errors, but no runtime LM Studio call was executed in this environment to benchmark performance of the larger default model.

## Validation (mandatory)
- Commands run:
  - `rg -n "qwen2.5-vl-7b-instruct|qwen3.6-35b-a3b" .env.example README.md docker-compose.yml src/photo_curator/config.py src/photo_curator/pipeline_v1.py`
  - `uv run --project . ruff check src/photo_curator/config.py src/photo_curator/pipeline_v1.py`
- Observed results:
  - Search confirms replacements landed and old string no longer appears in touched files.
  - Ruff check passed for touched Python files.

## Follow-up
- Next branch goals:
  - Optionally add a short model-selection note in docs for balancing quality vs latency.
- What to try next if unresolved:
  - If users report latency/timeouts, recommend smaller LM Studio model via env override and bump timeout.
