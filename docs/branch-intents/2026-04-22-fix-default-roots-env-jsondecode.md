# Branch Intent: 2026-04-22-fix-default-roots-env-jsondecode

## Quick Summary
- Branch: `2026-04-22-fix-default-roots-env-jsondecode`
- Purpose: Fix Python runner startup crash where `PHOTO_CURATOR_DEFAULT_ROOTS=/photos/library` is treated as JSON by `pydantic-settings` and fails before field coercion.
- Scan first: Use this branch when you are working on the same feature area or error pattern.



## Intent
- Fix Python runner startup crash where `PHOTO_CURATOR_DEFAULT_ROOTS=/photos/library` is treated as JSON by `pydantic-settings` and fails before field coercion.

## Scope
- In scope:
  - Make `default_roots` environment parsing accept plain CSV/path strings (e.g., `/photos/library`) without requiring JSON list syntax.
  - Keep existing support for JSON list and comma-separated formats through current validator.
- Out of scope:
  - Compose topology changes.
  - CLI contract changes.
  - Database/pipeline behavior changes.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-simplify-env-photo-roots.md`
  - `docs/branch-intents/2026-04-22-single-photo-ingest-root-env.md`
  - `docs/branch-intents/2026-04-22-fix-python-runner-libgl-opencv-headless.md`
- Relevant lessons pulled forward:
  - Keep startup fixes small and focused.
  - Avoid adding new env knobs; make current env values robust.
- Rabbit holes to avoid this time:
  - Reworking compose service wiring again for a parsing bug.

## Architecture decisions
- Decision:
  - Mark `Settings.default_roots` as `Annotated[list[str], NoDecode]` so env source does not JSON-decode this field before the validator runs.
- Why:
  - The current validator already handles string/list/JSON-list inputs safely; the crash happens earlier in the source decoding stage.
- Tradeoff:
  - `default_roots` skips automatic complex decoding and relies on explicit validator logic (already present), which is a small increase in custom parsing responsibility.

## Error log (mandatory)
- Exact error message(s):
  - `JSONDecodeError: Expecting value: line 1 column 1 (char 0)`
  - `SettingsError: error parsing value for field "default_roots" from source "EnvSettingsSource"`
- Where seen (command/log/file):
  - `mybestphotos-python-runner` container logs during CLI startup (`photo_curator.config.Settings` initialization path).
- Frequency or reproducibility notes:
  - Reproducible when `PHOTO_CURATOR_DEFAULT_ROOTS` is a plain path string like `/photos/library`.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Updated `src/photo_curator/config.py` to annotate `default_roots` with `NoDecode` and retain existing coercion validator.
  - Why this was tried:
    - Prevent pydantic env source from forcing JSON parse before custom parsing logic.
  - Result:
    - Patch applied successfully.
- Attempt 2:
  - Change made:
    - Tried to run an executable validation snippet via `uv run --project . python` to instantiate `Settings` with `PHOTO_CURATOR_DEFAULT_ROOTS=/photos/library`.
  - Why this was tried:
    - Confirm the startup path no longer throws `SettingsError`.
  - Result:
    - Validation blocked in this environment due to network tunnel failures while fetching dependencies from PyPI.
- Attempt 3:
  - Change made:
    - Added `CompatEnvSettingsSource` in `src/photo_curator/config.py` and wired it through `settings_customise_sources` to bypass env-source JSON decoding for `default_roots`.
  - Why this was tried:
    - Add a compatibility guard in case `NoDecode` behavior differs across `pydantic-settings` versions/environments and still attempts early JSON decoding.
  - Result:
    - Local direct validation with `python` succeeds for plain path, JSON list, CSV string, and empty string values.

## What went right (mandatory)
- Parsing fix is localized to one field and preserves existing accepted formats.

## What went wrong (mandatory)
- Could not run a full runtime validation command because dependency sync failed from network restrictions.

## Validation (mandatory)
- Commands run:
  - `python - <<'PY' ... PY`
  - `uv run --project . ruff check src/photo_curator/config.py`
- Observed results:
  - Direct `python` validation completed and showed correct coercion outcomes for supported env formats.
  - `uv run` command could not complete due to `Failed to fetch: https://pypi.org/simple/pgvector/` (network/tunnel error), so linting via project env remains blocked here.

## Follow-up
- Next branch goals:
  - Re-run startup validation in an environment with PyPI access and confirm docker runner starts cleanly.
- What to try next if unresolved:
  - If parsing still fails, inspect any additional list-typed settings for early env decoding behavior and annotate selectively with `NoDecode`.
