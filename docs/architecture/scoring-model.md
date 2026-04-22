# Scoring model (v1.2)

This project now tracks three interpretable score layers in `file_metrics`:

1. **technical_quality_score**
   - Derived from blur, contrast, brightness balance, entropy, and noise.
   - Intended to represent pure image quality independent of subject matter.

2. **semantic_relevance_score**
   - Lightweight signal based on description richness and extracted categories.
   - Keeps the score explainable until a dedicated semantic model is added.

3. **curation_score**
   - Final rank helper combining technical quality and semantic relevance.
   - Current formula is intentionally simple and transparent.

4. **nima_score / aesthetic_score / keep_score**
   - Advanced-runner outputs intended to represent aesthetics/photogenic quality.
   - `nima_score` is produced by a true NIMA metric backend (`pyiqa`) when available.
   - If runtime/model loading fails, the runner falls back to deterministic proxy scoring (`nima_style_v0`) and marks fallback in `nima_model_version`.
   - `aesthetic_score` and `keep_score` are derived from `nima_score` + technical quality for ranking workflows.

## Base vs advanced ownership

- `files` stores canonical file truth and stable extraction facts.
- Base deterministic metrics land in `file_metrics` during base ingest.
- Model-like or evolving enrichment (NIMA scoring, descriptions, future tags/captions) is treated as advanced runner output and expected to be rerun over time.

## Why not ML/ORM refactors yet?

- The current SQL+pipeline approach is stable and easy to inspect.
- Scoring improvements are additive and low risk.
- We avoid broad migrations until we observe clear maintainability pain.
