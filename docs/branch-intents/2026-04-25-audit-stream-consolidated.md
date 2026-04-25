# Branch Intent: 2026-04-25-audit-stream-consolidated

## Quick Summary
- Branch: `2026-04-25-audit-stream-consolidated`
- Purpose: Consolidate fragmented April 25 audit branch-intent notes into one canonical document and record current still-open issues.
- Scan first: Use this branch when you are working on the same feature area or error pattern.



## Intent
- Consolidate fragmented April 25 audit branch-intent notes into one canonical document and record current still-open issues.

## Scope
- In scope:
  - Merge the content focus of:
    - `2026-04-25-validate-what-is-still-valid.md`
    - `2026-04-25-fix-audit-items-without-input.md`
    - `2026-04-25-issues-a-to-e.md`
    - `2026-04-25-followup-validity-matrix-recheck.md`
  - Capture a concise “what is still open” status.
  - Remove redundant per-step files once consolidated.
- Out of scope:
  - Additional runtime/schema/UI behavior changes.

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-25-validate-what-is-still-valid.md`
  - `docs/branch-intents/2026-04-25-fix-audit-items-without-input.md`
  - `docs/branch-intents/2026-04-25-issues-a-to-e.md`
  - `docs/branch-intents/2026-04-25-followup-validity-matrix-recheck.md`
- Relevant lessons pulled forward:
  - Keep claims evidence-backed and separate “fixed” vs “still legacy by design.”
  - Keep branch-intent history readable; reduce file sprawl for one logical audit stream.
- Rabbit holes to avoid this time:
  - Re-implementing already-merged fixes instead of documenting final state.

## Architecture decisions
- Decision:
  - Use a single canonical branch-intent file for this audit stream and remove redundant sibling files.
- Why:
  - Improves navigability and keeps branch-intent chronology understandable.
- Tradeoff:
  - Granular per-step files are removed; this consolidated file now carries the summary trail.

## Error log (mandatory)
- Exact error message(s):
  - None in this consolidation pass.
- Where seen (command/log/file):
  - N/A.
- Frequency or reproducibility notes:
  - N/A.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Reviewed all April 25 branch-intent files tied to the audit/fix/recheck sequence.
  - Why this was tried:
    - Needed a complete source set before consolidation.
  - Result:
    - Successful; overlap and duplication identified.
- Attempt 2:
  - Change made:
    - Created this consolidated file and removed the four redundant files.
  - Why this was tried:
    - User requested cleanup and combination.
  - Result:
    - Successful; one canonical record remains.

## What went right (mandatory)
- Consolidation is documentation-only and low risk.
- The remaining open issue is clearly scoped.

## What went wrong (mandatory)
- No new runtime validation was executed in this pass.

## Validation (mandatory)
- Commands run:
  - `rg --files docs/branch-intents | sort`
  - `sed -n '1,220p' docs/branch-intents/TEMPLATE.md`
  - `sed -n '1,260p' docs/branch-intents/2026-04-25-validate-what-is-still-valid.md`
  - `sed -n '1,260p' docs/branch-intents/2026-04-25-fix-audit-items-without-input.md`
  - `sed -n '1,260p' docs/branch-intents/2026-04-25-issues-a-to-e.md`
  - `sed -n '1,260p' docs/branch-intents/2026-04-25-followup-validity-matrix-recheck.md`
- Observed results:
  - Inputs were present and suitable for consolidation.

## Current issue status (follow-up summary)
- Still present:
  - None of the original high-priority audit issues remain open after the legacy auto-config follow-up.
- No longer present (already addressed in prior April 25 fixes):
  - `select_top` unpack mismatch.
  - NIMA stddev centered on zero.
  - Technical scorer `force` SQL predicate bug.
  - Missing `pipeline_runs.run_id` uniqueness index.
  - Missing `aesthetic_score`/`keep_score` indexes.
  - No LM Studio retry handling for 429/transient failures.
  - No graceful API shutdown.
  - UI hardcoded personal-name suggested topics.
  - Legacy-table-only behavior for `select_top.py` and `technical.py` (now supports legacy + v1 schema mode detection).

## Follow-up
- Next branch goals:
  - If desired, replace legacy-table dependencies with `files/file_metrics` equivalents in legacy commands.
- What to try next if unresolved:
  - Implement v1-schema-backed replacements for `select_top` and `score_technical`, then deprecate legacy modules.
