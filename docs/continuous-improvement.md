# Continuous Improvement Loop

This document describes the repeatable process for improving the photo scoring system through evidence-based iteration.

## How It Works

Each pipeline run automatically:

1. **Creates a database record** in `pipeline_runs` with metadata (model version, ingest settings)
2. **Logs score distributions** to console after each stage (metrics + advanced)
3. **Stores distribution stats** (min/max/median/p25/p75/p90/stddev) per score field in the database
4. **Writes a JSON artifact** to `reports/run_<timestamp>_<run_id>.json` for file-based comparison

## Observing Score Distributions

After running the pipeline, look for these console outputs:

```
================================================================================
Metrics score distribution (processed=1500)
--------------------------------------------------------------------------------
  Blur                      n=1500   min=0.0234  p25=0.1567  median=0.4891  p75=0.7234  p90=0.8912  max=0.9876  stddev=0.2345
  Brightness                n=1500   min=0.1234  p25=0.3456  median=0.5678  p75=0.7890  p90=0.9012  max=0.9876  stddev=0.1876
  ...

================================================================================
Advanced score distribution
--------------------------------------------------------------------------------
   CLIP Aesthetic Score        n=1450   min=0.3456  p25=0.4567  median=0.5678  p75=0.6789  p90=0.7890  max=0.8901  stddev=0.1234
  Aesthetic Score           n=1450   min=0.3789  p25=0.4890  median=0.6012  p75=0.7123  p90=0.8234  max=0.9345  stddev=0.1345
  ...
```

### What to look for:

| Signal | Meaning | Action |
|--------|---------|--------|
| `stddev < 0.05` | Scores are too compressed — not discriminative enough | Widen normalization bounds or add new signals |
| `p25 == p75` (or very close) | Large cluster of identical scores | Investigate if this is expected for a subset of photos |
| Many NULL counts in advanced fields | Scoring pipeline didn't reach all files | Check runner logs for errors; increase ingest limit |
| Median far from 0.5 with narrow spread | Systematic bias (too high or too low) | Adjust scoring weights or thresholds |

## Running Diagnostics

### From the database:

```bash
# Run full diagnostic suite
psql -U photo_curator -d photo_curator -f scripts/diagnose_scores.sql

# Or run specific sections interactively
docker compose exec mybestphotos-postgres psql -U photo_curator -d photo_curator \
  -c "SELECT * FROM pipeline_runs ORDER BY id DESC LIMIT 5;"
```

### From the API:

```bash
curl http://localhost:8080/api/v1/health | jq .
# Returns: database status, last run info, file stats
```

## Comparing Runs

### Via database:

```sql
-- Compare key score distributions across runs
SELECT run_id, started_at,
       clip_aesthetic_min, clip_aesthetic_median, clip_aesthetic_max, clip_aesthetic_stddev,
       curation_min, curation_median, curation_max, curation_stddev
FROM pipeline_runs
WHERE status = 'completed' AND completed_at IS NOT NULL
ORDER BY id DESC LIMIT 3;
```

### Via JSON artifacts:

Files in `reports/run_*_*.json` contain full score distributions for each run. Compare them with any diff tool or script.

## Iteration Process

1. **Baseline**: Run pipeline, observe score distributions from console logs and diagnostic queries
2. **Identify issues**: Look for compressed scores (low stddev), NULL counts, clustering
3. **Make focused change**: Adjust one scoring parameter or add one new signal
4. **Rerun**: Execute `docker compose run --rm python-runner` + `docker compose run --rm python-advanced-runner`
5. **Compare**: Check console output for improved spread; run diagnostic queries to compare with prior runs
6. **Document**: Update this doc and branch-intent files with findings

## Key Score Fields Reference

| Field | Range | Meaning |
|-------|-------|---------|
| `blur_score` | 0-1 (higher = sharper) | Technical sharpness from Laplacian variance |
| `brightness_score` | 0-1 (optimal at ~0.55 mean gray) | Exposure quality |
| `contrast_score` | 0-1 (higher = more contrast) | Image contrast relative to 255 scale |
| `entropy_score` | 0-1 (higher = more complex histogram) | Information content / histogram complexity |
| `noise_score` | 0-1 (higher = less noise) | Noise proxy from Gaussian blur difference |
| `technical_quality_score` | 0-1 | Weighted combination of above technical metrics |
| `clip_aesthetic_score` | 0-1 | CLIP-based aesthetic signal ((ViT-H/14, prompt differential)) |
| `aesthetic_score` | 0-1 | Derived from CLIP-based `clip_aesthetic_score` + blur resistance |
| `keep_score` | 0-1 | Combined technical quality + aesthetics for ranking |
| `curation_score` | 0-1 | Final rank helper: 70% technical + 30% semantic relevance |
| `semantic_relevance_score` | 0-1 | Description richness + category bonus |

## Troubleshooting

### Scores all clustered around 0.5:

This typically means the normalization bounds in `_safe_norm()` are too wide for your dataset. Run diagnostics to find the actual min/max of each metric, then tighten the bounds.

### Many NULL aesthetic/keep/curation scores:

The advanced runner only processes files missing these scores. If you see many NULLs after a run:
1. Check `docker compose logs python-advanced-runner` for errors
2. Verify `/photos/library` is mounted correctly in the container
3. Run `score-clip-aesthetic --force-rescore-all` to force re-scoring

### Low semantic_relevance_score across all files:

The basic description provider generates short, metadata-only descriptions. For richer scores:
1. Set `PHOTO_CURATOR_DESCRIPTION_PROVIDER=lmstudio` and ensure LM Studio is reachable
2. Or improve the category pattern matching in `_CATEGORY_PATTERNS`
