# Scoring Model (v1.3) — updated 2026-04-26

This project tracks scores in two tables: `file_metrics` (system/CLIP-derived) and `file_llm_results` (LLM-generated). All API responses normalize scores to consistent scales.

## file_metrics columns (system scores, all 0–1 unless noted)

| Column | Scale | Source | Description |
|--------|-------|--------|-------------|
| `blur_score` | 0–1 | Base ingest (OpenCV) | Higher = more blur |
| `brightness_score` | 0–1 | Base ingest | Image brightness level |
| `contrast_score` | 0–1 | Base ingest | Image contrast level |
| `entropy_score` | 0–1 | Base ingest | Image entropy/detail richness |
| `noise_score` | 0–1 | Base ingest (advanced runner) | Noise level |
| `technical_quality_score` | 0–1 | Derived from blur, contrast, brightness balance, entropy | Pure image quality independent of subject matter |
| `semantic_relevance_score` | 0–1 | Derived from description richness and categories | Lightweight semantic signal |
| `curation_score` | 0–1 | Final rank score = weighted blend of aesthetic + keep + technical_quality + semantic_relevance | Primary sorting metric (default sort) |
| `clip_aesthetic_score` | 0–1 | CLIP-based aesthetic scoring (ViT-H/14, prompt differential) | Raw CLIP aesthetic signal |
| `aesthetic_score` | 0–1 | Derived from clip_aesthetic_score + blur resistance + power curve | Primary aesthetic score used in API/UI |
| `keep_score` | 0–1 | Derived from technical_quality + aesthetic_spread | Probability the photo should be kept |
| `llm_aesthetic_score` | 0–1 | Migrated from file_llm_results.aesthetic_score (divided by 100) | LLM-generated aesthetic score, normalized to 0-1 |
| `llm_wall_art_score` | 0–1 | Migrated from file_llm_results.wall_art_score (divided by 100) | LLM-generated wall art suitability score, normalized to 0-1 |

## file_llm_results columns (LLM scores, stored as original 0–100 values)

| Column | Scale | Source | Description |
|--------|-------|--------|-------------|
| `aesthetic_score` | 0–100 | LM Studio vision model | LLM aesthetic score (original scale, preserved for reference) |
| `wall_art_score` | 0–100 | LM Studio vision model | LLM wall art suitability score (original scale, preserved for reference) |

## API response scales

The API returns scores on these scales:

- **aestheticScore**: always 0–1 (from `file_metrics.aesthetic_score`)
- **wallArtScore**: always 0–100 (converted from `file_metrics.llm_wall_art_score * 100`)
- **curationScore**: always 0–1
- All technical scores (blur, brightness, contrast, entropy, noise): always 0–1

## Scoring formulas

### CLIP Aesthetic (`compute_clip_aesthetic` in `scoring.py`)
```
clip_aesthetic = clamp(0.85 * clip_score + 0.15 * composition_balance)
aesthetic_spread = clamp((0.82 * clip_aesthetic + 0.18 * (1 - blur))^0.9)
keep_spread = clamp((0.45 * technical_quality + 0.55 * aesthetic_spread)^0.9)
```

### Curation Score (`compute_curation_score` in `scoring.py`)
```
curation = clamp(0.4 * aesthetic + 0.3 * keep + 0.2 * tech_quality + 0.1 * semantic_relevance)
```

## Base vs advanced ownership

- **files**: canonical file truth (path, EXIF, dimensions, hash).
- **file_metrics**: all scores live here after the 2026-04-26 cleanup. Previously LLM scores were only in `file_llm_results`, requiring cross-table coalesce fallbacks.
- **file_llm_results**: source of truth for LLM-generated descriptions, tags, and original (0–100) scores. Also stores semantic embeddings for vector search.
- **file_descriptions**: deterministic metadata-based captions (non-LLM).
- **file_labels**: user labels (favorite, notes).

## Score distribution ranges (from current data, 2026-04-26)

| Score | Min | Max | Avg | Stddev warning threshold |
|-------|-----|-----|-----|--------------------------|
| clip_aesthetic_score | ~0.47 | ~0.68 | ~0.56 | stddev < 0.05 |
| aesthetic_score | ~0.47 | ~0.68 | ~0.56 | stddev < 0.05 |
| keep_score | ~0.37 | ~0.75 | ~0.56 | stddev < 0.05 |
| curation_score | ~0.39 | ~0.81 | ~0.58 | stddev < 0.05 |
| technical_quality_score | ~0.13 | ~0.79 | ~0.48 | stddev < 0.05 |
| llm_aesthetic_score (normalized) | 0.10 | 0.85 | 0.64 | — |
| llm_wall_art_score (normalized) | 0.10 | 0.90 | 0.58 | — |

## Reset / reseed process

To reset all scores and rerun the pipeline:

```bash
# Drop and recreate DB volume (keeps schema bootstrap intact)
docker compose down -v
docker compose up -d postgres

# Re-ingest files
docker compose run --rm python-runner

# Run advanced scoring (CLIP + keep_score)
docker compose run --rm python-advanced-runner

# Run LLM descriptions + scores
docker compose run --rm python-llm-runner
```

## Diagnostic queries

Score distributions and NULL analysis: `scripts/diagnose_scores.sql`
