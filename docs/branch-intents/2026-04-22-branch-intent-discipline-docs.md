# Branch Intent: work (legacy name)

## Quick Summary
- Purpose: Clean up and condense process documentation while preserving existing guidance.
- Keywords: branch, intent, discipline, docs
## Intent
- Clean up and condense process documentation while preserving existing guidance.
- Make branch-intent usage explicit and mandatory for every Codex task, including failed attempts.

## Scope
- In scope:
  - Documentation-only updates in repository root guidance and docs index/template files.
- Out of scope:
  - Application/runtime code changes.
  - Service-level behavior, API, or Docker Compose wiring.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-22-foundation-stack.md`
  - `docs/branch-intents/2026-04-22-fix-client-importmeta-env.md`
  - `docs/branch-intents/2026-04-22-restructure-services-stack.md`
  - `docs/branch-intents/2026-04-22-ui-screenshot-tooling.md`
- Relevant lessons pulled forward:
  - Preserve attempts + outcomes so repeated failures are visible across branches.
  - Keep validation notes explicit.
- Rabbit holes to avoid this time:
  - Rewriting architecture docs when request is specifically process documentation.

## Architecture decisions
- Decision:
  - Enforce branch-intent discipline in multiple high-signal docs (`AGENTS.md`, `coding_rules.txt`, `AI_GUIDE.md`, docs index, and template).
- Why:
  - Increases chance the requirement is seen in every Codex run context.
- Tradeoff:
  - Some intentional redundancy across docs.

## Error log (mandatory)
- Exact error message(s):
  - None encountered during this documentation task.
- Where seen (command/log/file):
  - N/A.
- Frequency or reproducibility notes:
  - N/A.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Updated `docs/README.md` and `docs/branch-intents/TEMPLATE.md` to require prior-intent review + detailed error/attempt logs.
  - Why this was tried:
    - Directly addresses repeat-failure/rabbit-hole concern in the user request.
  - Result:
    - Successful.
- Attempt 2:
  - Change made:
    - Added explicit mandatory branch-intent rules to `AGENTS.md`, `coding_rules.txt`, and `AI_GUIDE.md`.
  - Why this was tried:
    - Ensures the requirement is picked up automatically by tooling prompts and checklists.
  - Result:
    - Successful.

## What went right (mandatory)
- Requirement became explicit in all primary contributor instruction docs.
- Existing documentation topics were preserved while reorganizing process language.

## What went wrong (mandatory)
- No runtime or tooling failures surfaced, so this branch provides limited technical troubleshooting data.

## Validation (mandatory)
- Commands run:
  - `rg --files docs AGENTS.md coding_rules.txt AI_GUIDE.md`
  - `sed -n '1,220p' AGENTS.md`
  - `sed -n '1,260p' coding_rules.txt`
  - `sed -n '1,220p' AI_GUIDE.md`
  - `sed -n '1,260p' docs/README.md`
  - `sed -n '1,260p' docs/branch-intents/TEMPLATE.md`
- Observed results:
  - Branch-intent requirements present and consistent.

## Follow-up
- Next branch goals:
  - Consider adding a lightweight check (pre-commit or CI) that verifies a touched branch has an updated file under `docs/branch-intents/`.
- What to try next if unresolved:
  - Add a script that validates required sections in branch-intent files.
