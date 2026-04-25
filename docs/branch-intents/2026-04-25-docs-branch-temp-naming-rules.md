# Branch Intent: docs-branch-temp-naming-rules

## Quick Summary
- Purpose: Enforce clearer branch names and temp-file naming so work is easier to review and trace.
- Keywords: docs, branch-naming, temp-files, process
- Branch name rationale: Uses `docs-branch-temp-naming-rules` to explicitly describe this branch’s policy-focused documentation update.

## Intent
- Prevent generic branch names (like `work`) and ambiguous temp artifact names that reduce auditability.

## Scope
- In scope:
  - Update repository process docs to require descriptive branch names.
  - Add temp-file naming and cleanup guidance in docs/template.
- Out of scope:
  - CI/pipeline enforcement scripts.
  - Historical branch renaming.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-25-legacy-work-branch-log.md`
  - `docs/branch-intents/2026-04-22-branch-intent-discipline-docs.md`
- Relevant lessons pulled forward:
  - Process rules should appear in high-signal docs (`AGENTS.md`, docs index, and template) so they are hard to miss.
- Rabbit holes to avoid this time:
  - Avoid adding enforcement tooling in this patch; keep it as policy/doc-only.

## Architecture decisions
- Decision:
  - Add naming rules to process docs and branch-intent template rather than code-level checks.
- Why:
  - Fastest low-risk way to address immediate workflow quality issue.
- Tradeoff:
  - Relies on reviewer discipline until automated checks are added.

## Error log (mandatory)
- Exact error message(s):
  - None (policy/quality issue, not runtime failure).
- Where seen (command/log/file):
  - Observed naming pattern in branch history and branch-intent records.
- Frequency or reproducibility notes:
  - Repeated use of generic names made context difficult to scan.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Updated `AGENTS.md` with explicit prohibition on placeholder branch names and guidance for temp-file naming.
  - Why this was tried:
    - AGENTS is the first instruction surface read by AI contributors.
  - Result:
    - Rule is now explicit and includes concrete examples.
- Attempt 2:
  - Change made:
    - Updated `docs/README.md` and `docs/branch-intents/TEMPLATE.md` with branch naming rationale and temp-file tracking/removal fields.
  - Why this was tried:
    - Needed persistent workflow reminders in both policy docs and per-branch template.
  - Result:
    - Future branch-intent entries can record temp artifacts and avoid generic naming.

## What went right (mandatory)
- Patch stayed documentation-only and aligned with existing branch-intent process docs.

## What went wrong (mandatory)
- No automated guard exists yet, so compliance is still manual.

## Validation (mandatory)
- Commands run:
  - `git branch --show-current`
  - `git diff -- AGENTS.md docs/README.md docs/branch-intents/TEMPLATE.md docs/branch-intents/2026-04-25-docs-branch-temp-naming-rules.md`
- Observed results:
  - Branch name is descriptive and docs reflect new naming guidance.

## Temp files and artifacts
- Temp files created during this branch (if any):
  - None.
- Why they were needed:
  - N/A.
- Removed before merge? (yes/no + reason):
  - Yes; none created.

## Follow-up
- Next branch goals:
  - Add optional lint/check script to detect placeholder branch names and undocumented temp artifacts.
- What to try next if unresolved:
  - Add a pre-commit or CI rule that flags branch-intent title/branch names matching denylist (`work`, `tmp`, `misc`).
