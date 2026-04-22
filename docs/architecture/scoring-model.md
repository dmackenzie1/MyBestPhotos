# Scoring model (v1.1)

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

## Why not ML/ORM refactors yet?

- The current SQL+pipeline approach is stable and easy to inspect.
- Scoring improvements are additive and low risk.
- We avoid broad migrations until we observe clear maintainability pain.
