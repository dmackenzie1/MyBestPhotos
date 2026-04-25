# Branch Intent: docs-markdown-audit-cleanup

## Quick Summary
- Purpose: Clean up markdown documentation consistency, clarify the two README files, and retire ambiguous legacy `work.md` naming.
- Keywords: docs, markdown, readme, branch-intent, cleanup
- Branch name rationale: Explicitly states this is a docs-wide markdown audit/cleanup pass.

## Intent
- Reduce documentation confusion and make naming policy internally consistent.

## Scope
- In scope:
  - Clarify root vs docs README roles.
  - Rename legacy branch-intent file `work.md` to descriptive name.
  - Update stale references introduced by the rename.
- Out of scope:
  - Non-documentation code changes.
  - Automated lint/CI enforcement.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-25-docs-branch-temp-naming-rules.md`
  - `docs/branch-intents/2026-04-25-legacy-work-branch-log.md`
  - `docs/branch-intents/2026-04-22-branch-intent-discipline-docs.md`
- Relevant lessons pulled forward:
  - Place guidance in high-signal entry points and keep naming explicit.
- Rabbit holes to avoid this time:
  - Avoid broad policy rewrites and keep this as focused cleanup.

## Architecture decisions
- Decision:
  - Keep both README files, but explicitly document their different purposes.
- Why:
  - Root README is runbook-oriented; docs README is index/policy-oriented.
- Tradeoff:
  - Slight duplication remains, but intent is now explicit and discoverable.

## Error log (mandatory)
- Exact error message(s):
  - None.
- Where seen (command/log/file):
  - User feedback: confusion about having two README files and inconsistent doc naming.
- Frequency or reproducibility notes:
  - Reproducible for new contributors reading docs without context.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Added a “Documentation map” section in root README and a complement note in docs/README.
  - Why this was tried:
    - Resolve ambiguity directly where contributors start reading.
  - Result:
    - Purpose of both README files is now explicit.
- Attempt 2:
  - Change made:
    - Renamed `docs/branch-intents/work.md` to `docs/branch-intents/2026-04-25-legacy-work-branch-log.md` and updated references/headings.
  - Why this was tried:
    - Remove ambiguous filename while preserving historical content.
  - Result:
    - Branch-intent docs now better align with descriptive naming policy.

## What went right (mandatory)
- Local markdown link integrity remained valid after rename.

## What went wrong (mandatory)
- Legacy references to `work` still exist inside historical notes by design and are now explicitly marked as legacy.

## Validation (mandatory)
- Commands run:
  - `python - <<'PY' ...` (local markdown link existence check excluding node_modules)
  - `git diff --check`
- Observed results:
  - No missing local markdown links.
  - No whitespace errors.

## Temp files and artifacts
- Temp files created during this branch (if any):
  - None.
- Why they were needed:
  - N/A.
- Removed before merge? (yes/no + reason):
  - Yes; none created.

## Follow-up
- Next branch goals:
  - Add an optional docs lint script that flags ambiguous branch-intent filenames.
- What to try next if unresolved:
  - Add CI check to deny newly-added `work.md`/`tmp.md` style branch-intent files.
