-- ============================================================================
-- MyBestPhotos Diagnostic Queries
-- Run with: psql -U photo_curator -d photo_curator -f scripts/diagnose_scores.sql
-- Or interactively in any SQL client connected to the database.
-- ============================================================================

-- 1. SYSTEM HEALTH
-- ----------------------------------------------------------------------------
\echo '=== SYSTEM HEALTH ==='

SELECT 'files' AS table_name, COUNT(*)::int AS row_count FROM files
UNION ALL
SELECT 'file_metrics', COUNT(*) FROM file_metrics
UNION ALL
SELECT 'file_descriptions', COUNT(*) FROM file_descriptions
UNION ALL
SELECT 'file_labels', COUNT(*) FROM file_labels;

-- 2. SCORE NULL ANALYSIS (how many files are missing each score?)
-- ----------------------------------------------------------------------------
\echo ''
\echo '=== SCORE NULL ANALYSIS ==='

SELECT
    COUNT(*) FILTER (WHERE blur_score IS NULL) AS blur_null,
    COUNT(*) FILTER (WHERE brightness_score IS NULL) AS brightness_null,
    COUNT(*) FILTER (WHERE contrast_score IS NULL) AS contrast_null,
    COUNT(*) FILTER (WHERE entropy_score IS NULL) AS entropy_null,
    COUNT(*) FILTER (WHERE noise_score IS NULL) AS noise_null,
    COUNT(*) FILTER (WHERE technical_quality_score IS NULL) AS tech_quality_null,
    COUNT(*) FILTER (WHERE clip_aesthetic_score IS NULL) AS clip_aesthetic_null,
    COUNT(*) FILTER (WHERE aesthetic_score IS NULL) AS aesthetic_null,
    COUNT(*) FILTER (WHERE keep_score IS NULL) AS keep_null,
    COUNT(*) FILTER (WHERE curation_score IS NULL) AS curation_null,
    COUNT(*) FILTER (WHERE semantic_relevance_score IS NULL) AS semantic_null,
    COUNT(*) FILTER (WHERE llm_aesthetic_score IS NULL) AS llm_aesthetic_null,
    COUNT(*) FILTER (WHERE llm_wall_art_score IS NULL) AS llm_wall_art_null
FROM file_metrics;

-- 3. SCORE DISTRIBUTIONS (current state)
-- ----------------------------------------------------------------------------
\echo ''
\echo '=== CURRENT SCORE DISTRIBUTIONS ==='

SELECT
    'clip_aesthetic_score' AS score_field,
    COUNT(*)::int AS n,
    MIN(clip_aesthetic_score)::numeric(10,4) AS min_val,
    MAX(clip_aesthetic_score)::numeric(10,4) AS max_val,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY clip_aesthetic_score)::numeric(10,4) AS p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY clip_aesthetic_score)::numeric(10,4) AS median,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY clip_aesthetic_score)::numeric(10,4) AS p75,
    PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY clip_aesthetic_score)::numeric(10,4) AS p90,
    STDDEV(clip_aesthetic_score)::numeric(10,6) AS stddev
FROM file_metrics WHERE clip_aesthetic_score IS NOT NULL

UNION ALL

SELECT
    'aesthetic_score',
    COUNT(*)::int,
    MIN(aesthetic_score)::numeric(10,4),
    MAX(aesthetic_score)::numeric(10,4),
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY aesthetic_score)::numeric(10,4),
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY aesthetic_score)::numeric(10,4),
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY aesthetic_score)::numeric(10,4),
    PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY aesthetic_score)::numeric(10,4),
    STDDEV(aesthetic_score)::numeric(10,6)
FROM file_metrics WHERE aesthetic_score IS NOT NULL

UNION ALL

SELECT
    'keep_score',
    COUNT(*)::int,
    MIN(keep_score)::numeric(10,4),
    MAX(keep_score)::numeric(10,4),
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY keep_score)::numeric(10,4),
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY keep_score)::numeric(10,4),
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY keep_score)::numeric(10,4),
    PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY keep_score)::numeric(10,4),
    STDDEV(keep_score)::numeric(10,6)
FROM file_metrics WHERE keep_score IS NOT NULL

UNION ALL

SELECT
    'curation_score',
    COUNT(*)::int,
    MIN(curation_score)::numeric(10,4),
    MAX(curation_score)::numeric(10,4),
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY curation_score)::numeric(10,4),
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY curation_score)::numeric(10,4),
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY curation_score)::numeric(10,4),
    PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY curation_score)::numeric(10,4),
    STDDEV(curation_score)::numeric(10,6)
FROM file_metrics WHERE curation_score IS NOT NULL

UNION ALL

SELECT
    'technical_quality_score',
    COUNT(*)::int,
    MIN(technical_quality_score)::numeric(10,4),
    MAX(technical_quality_score)::numeric(10,4),
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY technical_quality_score)::numeric(10,4),
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY technical_quality_score)::numeric(10,4),
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY technical_quality_score)::numeric(10,4),
    PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY technical_quality_score)::numeric(10,4),
    STDDEV(technical_quality_score)::numeric(10,6)
FROM file_metrics WHERE technical_quality_score IS NOT NULL

UNION ALL

SELECT
    'semantic_relevance_score',
    COUNT(*)::int,
    MIN(semantic_relevance_score)::numeric(10,4),
    MAX(semantic_relevance_score)::numeric(10,4),
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY semantic_relevance_score)::numeric(10,4),
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY semantic_relevance_score)::numeric(10,4),
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY semantic_relevance_score)::numeric(10,4),
    PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY semantic_relevance_score)::numeric(10,4),
    STDDEV(semantic_relevance_score)::numeric(10,6)
FROM file_metrics WHERE semantic_relevance_score IS NOT NULL

UNION ALL

SELECT
    'llm_aesthetic_score',
    COUNT(*)::int,
    MIN(llm_aesthetic_score)::numeric(10,4),
    MAX(llm_aesthetic_score)::numeric(10,4),
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY llm_aesthetic_score)::numeric(10,4),
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY llm_aesthetic_score)::numeric(10,4),
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY llm_aesthetic_score)::numeric(10,4),
    PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY llm_aesthetic_score)::numeric(10,4),
    STDDEV(llm_aesthetic_score)::numeric(10,6)
FROM file_metrics WHERE llm_aesthetic_score IS NOT NULL

UNION ALL

SELECT
    'llm_wall_art_score',
    COUNT(*)::int,
    MIN(llm_wall_art_score)::numeric(10,4),
    MAX(llm_wall_art_score)::numeric(10,4),
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY llm_wall_art_score)::numeric(10,4),
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY llm_wall_art_score)::numeric(10,4),
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY llm_wall_art_score)::numeric(10,4),
    PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY llm_wall_art_score)::numeric(10,4),
    STDDEV(llm_wall_art_score)::numeric(10,6)
FROM file_metrics WHERE llm_wall_art_score IS NOT NULL;

-- 4. SCORE CLUSTERING CHECK (how many files fall in narrow bands?)
-- ----------------------------------------------------------------------------
\echo ''
\echo '=== SCORE CLUSTERING CHECK ==='
\echo '(Files falling within the tightest 5% band — indicates compression)'

SELECT
    score_field,
    COUNT(*) AS files_in_tightest_band,
    ROUND(COUNT(*) * 100.0 / total_count, 2) AS pct_of_total
FROM (
    SELECT 'clip_aesthetic_score' AS score_field, clip_aesthetic_score AS val FROM file_metrics WHERE clip_aesthetic_score IS NOT NULL
    UNION ALL
    SELECT 'aesthetic_score', aesthetic_score FROM file_metrics WHERE aesthetic_score IS NOT NULL
    UNION ALL
    SELECT 'keep_score', keep_score FROM file_metrics WHERE keep_score IS NOT NULL
    UNION ALL
    SELECT 'curation_score', curation_score FROM file_metrics WHERE curation_score IS NOT NULL
    UNION ALL
    SELECT 'technical_quality_score', technical_quality_score FROM file_metrics WHERE technical_quality_score IS NOT NULL
    UNION ALL
    SELECT 'semantic_relevance_score', semantic_relevance_score FROM file_metrics WHERE semantic_relevance_score IS NOT NULL
    UNION ALL
    SELECT 'llm_aesthetic_score', llm_aesthetic_score FROM file_metrics WHERE llm_aesthetic_score IS NOT NULL
    UNION ALL
    SELECT 'llm_wall_art_score', llm_wall_art_score FROM file_metrics WHERE llm_wall_art_score IS NOT NULL
) scores
JOIN (
    SELECT score_field, COUNT(*) AS total_count
    FROM (
        SELECT 'clip_aesthetic_score' AS score_field FROM file_metrics WHERE clip_aesthetic_score IS NOT NULL
        UNION ALL SELECT 'aesthetic_score' FROM file_metrics WHERE aesthetic_score IS NOT NULL
        UNION ALL SELECT 'keep_score' FROM file_metrics WHERE keep_score IS NOT NULL
        UNION ALL SELECT 'curation_score' FROM file_metrics WHERE curation_score IS NOT NULL
        UNION ALL SELECT 'technical_quality_score' FROM file_metrics WHERE technical_quality_score IS NOT NULL
        UNION ALL SELECT 'semantic_relevance_score' FROM file_metrics WHERE semantic_relevance_score IS NOT NULL
        UNION ALL SELECT 'llm_aesthetic_score' FROM file_metrics WHERE llm_aesthetic_score IS NOT NULL
        UNION ALL SELECT 'llm_wall_art_score' FROM file_metrics WHERE llm_wall_art_score IS NOT NULL
    ) sub
    GROUP BY score_field
) totals ON scores.score_field = totals.score_field
GROUP BY score_field, total_count;

-- 5. TOP AND BOTTOM SCORED FILES
-- ----------------------------------------------------------------------------
\echo ''
\echo '=== TOP 10 CURATION SCORE ==='
SELECT f.id, f.filename, fm.curation_score, fm.aesthetic_score, fm.llm_aesthetic_score,
       fm.keep_score, fm.technical_quality_score, fm.semantic_relevance_score,
       f.camera_make, f.camera_model, f.photo_taken_at
FROM files f
JOIN file_metrics fm ON fm.file_id = f.id
WHERE fm.curation_score IS NOT NULL
ORDER BY fm.curation_score DESC NULLS LAST
LIMIT 10;

\echo ''
\echo '=== BOTTOM 10 CURATION SCORE ==='
SELECT f.id, f.filename, fm.curation_score, fm.aesthetic_score, fm.llm_aesthetic_score,
       fm.keep_score, fm.technical_quality_score,
       f.camera_make, f.camera_model, f.photo_taken_at
FROM files f
JOIN file_metrics fm ON fm.file_id = f.id
WHERE fm.curation_score IS NOT NULL
ORDER BY fm.curation_score ASC NULLS FIRST
LIMIT 10;

-- 6. PIPELINE RUN HISTORY
-- ----------------------------------------------------------------------------
\echo ''
\echo '=== LAST 5 PIPELINE RUNS ==='
SELECT
    id,
    run_id,
    started_at,
    completed_at,
    EXTRACT(EPOCH FROM (completed_at - started_at))::int AS duration_seconds,
    status,
    clip_model_version,
    total_files_ingested,
    total_metrics_scored,
    total_clip_aesthetic_scored,
    total_described,
    total_skipped,
    total_failed,
    notes
FROM pipeline_runs
WHERE completed_at IS NOT NULL
ORDER BY id DESC
LIMIT 5;

-- 7. SCORE COMPARISON ACROSS RUNS (key metrics)
-- ----------------------------------------------------------------------------
\echo ''
\echo '=== SCORE COMPARISON: LAST 3 COMPLETED RUNS ==='
SELECT
    run_id,
    started_at,
    total_files_ingested,
    clip_aesthetic_min, clip_aesthetic_median, clip_aesthetic_max, clip_aesthetic_stddev,
    aesthetic_min, aesthetic_median, aesthetic_max, aesthetic_stddev,
    keep_min, keep_median, keep_max, keep_stddev,
    curation_min, curation_median, curation_max, curation_stddev,
    semantic_relevance_min, semantic_relevance_median, semantic_relevance_max, semantic_relevance_stddev,
    notes
FROM pipeline_runs
WHERE status = 'completed' AND completed_at IS NOT NULL
ORDER BY id DESC
LIMIT 3;

-- 8. CAMERA MODEL BREAKDOWN (how many files per camera?)
-- ----------------------------------------------------------------------------
\echo ''
\echo '=== FILES PER CAMERA ==='
SELECT
    COALESCE(camera_make, '(unknown)') AS make,
    COALESCE(camera_model, '(unknown)') AS model,
    COUNT(*)::int AS file_count,
    COUNT(*) FILTER (WHERE fm.aesthetic_score IS NOT NULL)::int AS scored_count,
    ROUND(AVG(fm.curation_score)::numeric, 3) AS avg_curation,
    ROUND(STDDEV(fm.curation_score)::numeric, 3) AS stddev_curation
FROM files f
LEFT JOIN file_metrics fm ON fm.file_id = f.id
GROUP BY camera_make, camera_model
ORDER BY file_count DESC
LIMIT 20;

-- 9. DATE RANGE AND PHOTO COUNT
-- ----------------------------------------------------------------------------
\echo ''
\echo '=== DATE RANGE ==='
SELECT
    MIN(photo_taken_at)::date AS earliest_date,
    MAX(photo_taken_at)::date AS latest_date,
    COUNT(*)::int AS total_photos
FROM files
WHERE photo_taken_at IS NOT NULL;

-- 10. DUPLICATE ANALYSIS (by filename and SHA256)
-- ----------------------------------------------------------------------------
\echo ''
\echo '=== POTENTIAL DUPLICATES BY FILENAME ==='
SELECT filename, COUNT(*)::int AS count
FROM files
GROUP BY filename
HAVING COUNT(*) > 1
ORDER BY count DESC
LIMIT 20;

\echo ''
\echo '=== POTENTIAL DUPLICATES BY SHA256 ==='
SELECT sha256, COUNT(*)::int AS count
FROM files
GROUP BY sha256
HAVING COUNT(*) > 1
ORDER BY count DESC
LIMIT 20;
