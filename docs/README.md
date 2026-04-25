# Documentation Index

This index is intentionally short: it points to the stable architecture docs and the required branch-intent workflow.

## Core architecture docs
- `docs/architecture/stack-overview.md`
- `docs/architecture/api-contract.md`
- `docs/architecture/runner-notes.md`

## Process docs
- `docs/continuous-improvement.md` — How to observe score distributions, run diagnostics, and iterate on scoring improvements.

## Branch-intent docs
- `docs/branch-intents/TEMPLATE.md`
- `docs/branch-intents/*.md`

## Branch-intent workflow (default policy)
Branch-intent docs are required for meaningful work, but we now use a lightweight exception for tiny edits:

1. **When a branch-intent file is required**
   - Required for substantive changes (multi-file, non-trivial behavior/config updates, debugging, refactors, or anything beyond a typo/one-line touch-up).
   - Not required for typo-only or obvious one-line fixes.

2. **One branch-intent file per branch**
   - Keep a single branch-intent file for each branch.
   - If multiple attempts happen on the same branch, append/update the same file instead of creating a new one.

3. **Before making changes**
   - Review existing `docs/branch-intents/*.md` for related errors, failed attempts, and rabbit-hole signals.
   - Start by scanning headers (`# Branch Intent` + `## Quick Summary`) to quickly triage relevance.
   - Summarize what prior attempts you are reusing or explicitly avoiding.

4. **During implementation**
   - Keep notes of what was tried, exact error messages, why a path was chosen, and why alternatives were rejected.

5. **Before handoff/merge**
   - Add or update the branch-intent file for the current branch using the template.
   - Ensure the file captures:
     - quick summary at the top for fast scanning
     - intent and scope
     - exact error text encountered
     - attempted fixes and outcomes (including failures)
     - validation commands + observed results
     - follow-up ideas for the next branch

6. **Simple titles**
   - Keep branch-intent titles, branch names, and merge-request titles short, plain, and easy to scan.
