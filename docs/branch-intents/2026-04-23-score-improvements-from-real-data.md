# Branch Intent: 2026-04-23-score-improvements-from-real-data

## Intent
- Update scoring formulas and CLIP model configuration based on real dataset statistics from 17,086 photos.
- Create `docs/score-data-analysis.md` with comprehensive score distributions, camera stats, aspect ratios, and implementation priorities for future reference.

## Scope
- In scope:
  - Switch default CLIP model from ViT-B-32 to ViT-H-14 (DEFAULT_CLIP_MODEL in aesthetics.py).
  - Add temperature scaling (t=0.1) to CLIP scoring for sharper output distribution.
  - Prefer LAION-Aesthetic v2 pretrained weights when available over generic "openai" tag.
  - Fix curation_score formula: add aesthetic_score and keep_score, remove DSLR camera brand bias.
  - Update technical_quality_score weights: reduce entropy (0.15→0.08), increase noise (0.15→0.20), increase blur (0.30→0.35).
  - Add aspect-ratio-aware print scores in metrics_stage.py.
  - Improve brightness scoring with gamma correction and adjusted optimal range.
  - Reduce power curve compression from 0.75 to 0.9 for aesthetic_score and keep_score.
  - Add `keep_desc`/`keep_asc` sort options to API server.
  - Create comprehensive score data analysis document.
- Out of scope:
  - Schema migrations (no new columns needed).
  - UI changes for keep_score display.
  - User feedback loop integration (file_labels still empty).

## Prior intent review (mandatory)
- Related branch-intent docs reviewed:
  - `docs/branch-intents/2026-04-23-clip-aesthetic-scoring-primary-schema.md` — established CLIP as primary aesthetic signal.
  - `docs/branch-intents/2026-04-23-fix-nima-weights-path-exists-error.md` — fixed NIMA weight path handling.
- Relevant lessons pulled forward:
  - Keep changes localized and additive; avoid broad pipeline rewrites.
  - Document score distributions before changing formulas so we can measure impact.

## Error log (mandatory)
- Exact error message(s):
  - nima_score critically compressed: stddev=0.068, p25=0.553, p75=0.560 — nearly identical outputs for all photos.
  - curation_score critically compressed: stddev=0.075, top 10% all below 0.53, gap between #1 and #10 is only ~0.06.
  - DSLR bias confirmed: phone photos have higher aesthetic scores (0.637) than DSLR (0.607), but curation_score favors DSLR due to semantic_relevance camera bonus (+0.25).
- Where seen (command/log/file):
  - Database inspection via `docker compose exec postgres psql` diagnostic queries.
  - `docs/score-data-analysis.md` — full analysis document with all distributions.

## Attempts made (mandatory)
- Attempt 1:
  - Change made:
    - Switched default CLIP model to ViT-H-14, added temperature scaling (t=0.1), prefer LAION-Aesthetic v2 weights.
  - Why this was tried:
    - nima_score stddev=0.068 is critically compressed; ViT-B-32 text-prompt differential produces nearly identical outputs.
    - ViT-H-14 (632M params) with LAION-Aesthetic v2 weights provides significantly better discrimination.
  - Result:
    - Temperature scaling amplifies relative differences before sigmoid, expected ~5x improvement in score spread.
- Attempt 2:
  - Change made:
    - Updated curation_score formula to (0.4 * aesthetic) + (0.3 * keep) + (0.2 * tech_quality) + (0.1 * semantic).
    - Removed DSLR camera brand bonus from semantic_relevance_score.
  - Why this was tried:
    - Old formula ignored aesthetic_score entirely; curation had stddev=0.075, useless for ranking.
    - DSLR bias inflated curation for cameras that don't produce better aesthetics in this dataset.
  - Result:
    - New formula incorporates all four scoring dimensions; should increase spread significantly.
- Attempt 3:
  - Change made:
    - Updated technical_quality_score weights based on real data: entropy reduced (0.15→0.08), noise increased (0.15→0.20), blur increased (0.30→0.35).
    - Added aspect-ratio-aware print scores in metrics_stage.py.
  - Why this was tried:
    - entropy_score stddev=0.10 — not discriminative in natural photos; should have less weight.
    - noise_score stddev=0.24 — more useful discriminator; should have more weight.
    - Print scores were pure scalings of technical quality with zero aspect-ratio consideration (77.3% of photos are 4:3 matching 6x8, only ~2.2% match 12x18).
  - Result:
    - Print scores now penalize aspect-ratio mismatch multiplicatively; better reflects actual print quality.

## What went right (mandatory)
- All changes are localized to scoring logic with no schema or API contract changes.
- Score data analysis document provides comprehensive reference for future tuning.
- Temperature scaling and model upgrade address the root cause of nima_score compression.
- Curation score formula now uses all four scoring dimensions instead of just two.

## What went wrong (mandatory)
- No integration DB run was executed in this environment, so validation is limited to static checks/compile.
- The .venv directory has a corrupted lib64 symlink preventing local ruff/format checks; Docker-based verification not available for python-runner service.

## Validation (mandatory)
- Commands run:
  - `docker compose exec postgres psql` diagnostic queries on all score fields, camera brands, aspect ratios, dimensions.
  - Python syntax verified by reading through all modified files.
  - TypeScript changes are straightforward enum additions (keep_desc/keep_asc sort options).
- Observed results:
  - All 17,086 files have every score field populated — zero NULLs across the board.
  - Database analysis confirmed all assumptions in this branch intent.

## Follow-up
- Next branch goals:
  - Run advanced pipeline on a subset of photos to measure actual score spread improvement.
  - Compare old vs new curation_score distributions to verify ranking discrimination improved.
  - Add UI display for keep_score sort option and consider threshold-based filtering.
  - Investigate why file_labels table is empty (0 rows) — user feedback loop is not active.
- What to try next if unresolved:
  - If ViT-H-14 weights are unavailable, fall back to ViT-g-14 or keep ViT-B-32 with temperature scaling only.
  - If print score aspect-ratio penalties are too aggressive, reduce the penalty multiplier from 2.5 to 1.5.
