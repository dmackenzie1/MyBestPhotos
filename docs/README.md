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

## Mandatory branch-intent workflow (every Codex task)
Every Codex task must include a branch-intent cycle, not only merge-time bookkeeping:

1. **Before making changes**
   - Review existing `docs/branch-intents/*.md` for related errors, failed attempts, and rabbit-hole signals.
   - Summarize what prior attempts you are reusing or explicitly avoiding.

2. **During implementation**
   - Keep notes of what was tried, exact error messages, why a path was chosen, and why alternatives were rejected.

3. **Before handoff/merge**
   - Add or update a branch-intent file for the current branch using the template.
   - Ensure the file captures:
     - intent and scope
     - exact error text encountered
     - attempted fixes and outcomes (including failures)
     - validation commands + observed results
     - follow-up ideas for the next branch

This requirement is **mandatory for each task**, even when a fix fails or is partial.
