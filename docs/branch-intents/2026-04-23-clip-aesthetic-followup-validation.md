# Branch Intent: 2026-04-23-clip-aesthetic-followup-validation

## Quick Summary
- Purpose: Validate the new CLIP aesthetic scoring path and confirm whether model weights are available/downloadable in this environment.
- Keywords: clip, aesthetic, followup, validation
## Intent
- Validate the new CLIP aesthetic scoring path and confirm whether model weights are available/downloadable in this environment.

## Scope
- In scope:
  - Re-check implementation details around CLIP model loading and runtime dependencies.
  - Run focused commands to verify model instantiation behavior.
  - Apply minimal fixes if follow-up issues are found.
- Out of scope:
  - Broad scoring redesign or schema changes.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-23-clip-aesthetic-scoring-primary-schema.md`
  - `docs/branch-intents/2026-04-23-fix-nima-weights-path-exists-error.md`
- Relevant lessons pulled forward:
  - Keep fixes localized and verify actual runtime behavior, not just static lint.
- Rabbit holes to avoid this time:
  - Avoid unrelated refactors.

## Architecture decisions
- Decision:
  - Resolve a pretrained CLIP tag automatically (`openai` preferred, else first available for the model) and load with explicit `pretrained=...`.
- Why:
  - `create_model_and_transforms(model_name)` in this environment loads a random-init model (no pretrained weights), which defeats aesthetic scoring quality.
- Tradeoff:
  - Runtime now explicitly depends on successful weight download/cache availability and fails fast with a clear message when unavailable.

## Error log (mandatory)
- Exact error message(s):
  - `WARNING:root:No pretrained weights loaded for model 'ViT-B-32'. Model initialized randomly.`
  - `RuntimeError: Failed to download weights for tag 'openai' ... 403 Forbidden`
- Where seen (command/log/file):
  - Ad-hoc `uv run --project . python` validation snippets invoking `open_clip.create_model_and_transforms(...)` and `load_clip_aesthetic_scorer(...)`.
- Frequency or reproducibility notes:
  - Reproduces consistently in this environment due outbound model-download restrictions (403 via proxy).

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Ran runtime checks comparing implicit CLIP load vs explicit pretrained tags.
  - Why this was tried:
    - Verify whether pretrained weights were actually being loaded.
  - Result:
    - Found implicit load warning and confirmed explicit downloads currently fail in this environment.
- Attempt 2:
  - Change made:
    - Updated `src/photo_curator/aesthetics.py` `_resolve_clip` to choose a pretrained tag and call `create_model_and_transforms(..., pretrained=tag)`.
  - Why this was tried:
    - Ensure production code requests real pretrained weights rather than random init.
  - Result:
    - Successful code change; behavior now explicit.
- Attempt 3:
  - Change made:
    - Added clear `RuntimeError` wrapper message instructing to fix Hugging Face access or pre-populate cache.
  - Why this was tried:
    - Provide actionable diagnostics when model download is blocked.
  - Result:
    - Successful; runtime failure now clear and intentional.

## What went right (mandatory)
- Validation caught a real quality bug: implicit CLIP load was random-init in this environment.
- Code now fails loudly with an actionable message instead of silently scoring with untrained weights.

## What went wrong (mandatory)
- Environment cannot currently download pretrained CLIP weights (`403 Forbidden`), so end-to-end scoring cannot be validated here.

## Validation (mandatory)
- Commands run:
  - `uv run --project . python - <<'PY' ... open_clip.list_models/list_pretrained checks ... PY`
  - `uv run --project . python - <<'PY' ... create_model_and_transforms implicit vs pretrained=None ... PY`
  - `uv run --project . python - <<'PY' ... try pretrained tags openai/laion... ... PY`
  - `uv run --project . ruff check src/photo_curator/aesthetics.py`
  - `uv run --project . python - <<'PY' ... load_clip_aesthetic_scorer('ViT-B-32','auto') ... PY`
- Observed results:
  - Implicit load can produce random-init warning.
  - Explicit pretrained downloads fail with 403 in this environment.
  - Lint passes and error messaging is now explicit.

## Follow-up
- Next branch goals:
  - Add optional config for explicit `clip_pretrained_tag` if operators want deterministic tag selection.
- What to try next if unresolved:
  - Ensure host/container has outbound access to Hugging Face (or mirrored artifact store) and warm cache before running scoring.
