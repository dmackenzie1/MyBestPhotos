# Branch Intent: 2026-04-22-update-lmstudio-default-base-url-to-lan-host

## Intent
- Address follow-up feedback by aligning LM Studio base URL defaults to the provided LAN endpoint (`http://192.168.10.64:1234/v1`) across config and documentation.

## Scope
- In scope:
  - Update default LM Studio base URL in env examples, compose defaults, and Python defaults.
  - Update README LM Studio setup text to reflect the LAN-host default.
- Out of scope:
  - Network autodiscovery or runtime endpoint health-check logic.
  - Changes to model selection behavior.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-update-lmstudio-default-model-qwen3.6-35b-a3b.md`
  - `docs/branch-intents/2026-04-22-ingest-consistency-and-db-lifecycle.md`
- Relevant lessons pulled forward:
  - Keep follow-up patch minimal and only adjust requested defaults.
  - Ensure docs + runtime defaults remain synchronized.
- Rabbit holes to avoid this time:
  - Avoid broader LM Studio integration refactors.

## Architecture decisions
- Decision:
  - Use `http://192.168.10.64:1234/v1` as the default LM Studio base URL across all existing default surfaces.
- Why:
  - User explicitly provided this endpoint as an additional required default.
- Tradeoff:
  - This LAN-specific default is less portable than loopback/host alias defaults, but can still be overridden by env vars/CLI.

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
    - Replaced existing LM Studio base URL defaults (`host.docker.internal` and `127.0.0.1`) with `192.168.10.64` in `.env.example`, `README.md`, `docker-compose.yml`, `src/photo_curator/config.py`, and `src/photo_curator/pipeline_v1.py`.
  - Why this was tried:
    - Ensure all default entry points reflect the endpoint provided in follow-up feedback.
  - Result:
    - Successful; all targeted defaults now use the provided LAN endpoint.
- Attempt 2:
  - Change made:
    - Updated the README note beneath LM Studio settings to avoid implying `host.docker.internal` is still the primary default.
  - Why this was tried:
    - Keep explanatory text consistent with the new LAN-host default while preserving alternative guidance.
  - Result:
    - Successful; docs now describe LAN URL as default and `host.docker.internal` as an option.

## What went right (mandatory)
- All known default URL references were updated consistently across docs and runtime configuration.

## What went wrong (mandatory)
- No integration test against live LM Studio endpoint was executed in this environment.

## Validation (mandatory)
- Commands run:
  - `rg -n "host.docker.internal:1234/v1|127.0.0.1:1234/v1|192.168.10.64:1234/v1" .env.example README.md docker-compose.yml src/photo_curator/config.py src/photo_curator/pipeline_v1.py`
  - `ruff check src/photo_curator/config.py src/photo_curator/pipeline_v1.py`
- Observed results:
  - Old default URL strings no longer appear in touched files; new URL appears in all default surfaces.
  - Ruff checks passed.

## Follow-up
- Next branch goals:
  - If portability concerns arise, add a short README note about choosing host alias vs LAN IP.
- What to try next if unresolved:
  - Revert defaults to host alias and document LAN override explicitly.
