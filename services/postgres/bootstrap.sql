-- Idempotent schema bootstrap: safe to run on every startup.
-- All statements use IF NOT EXISTS / ON CONFLICT so repeated runs are no-ops.
-- This file is mounted into the postgres-bootstrap container and executed
-- via psql before app-server and python-runner start, ensuring tables exist
-- on both fresh volumes (where init/001_stock_schema.sql also applies) and
-- existing volumes (where init scripts are skipped).

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS files (
  id BIGSERIAL PRIMARY KEY,
  source_root TEXT NOT NULL,
  relative_path TEXT NOT NULL,
  filename TEXT NOT NULL,
  extension TEXT NOT NULL,
  mime_type TEXT,
  file_size_bytes BIGINT NOT NULL,
  sha256 TEXT NOT NULL,
  width INTEGER,
  height INTEGER,
  orientation INTEGER,
  photo_taken_at TIMESTAMPTZ,
  photo_taken_at_source TEXT,
  camera_make TEXT,
  camera_model TEXT,
  gps_lat DOUBLE PRECISION,
  gps_lon DOUBLE PRECISION,
  exif_json JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (source_root, relative_path)
);

CREATE TABLE IF NOT EXISTS file_metrics (
  file_id BIGINT PRIMARY KEY REFERENCES files(id) ON DELETE CASCADE,
  blur_score DOUBLE PRECISION,
  brightness_score DOUBLE PRECISION,
  contrast_score DOUBLE PRECISION,
  entropy_score DOUBLE PRECISION,
  noise_score DOUBLE PRECISION,
  technical_quality_score DOUBLE PRECISION,
  semantic_relevance_score DOUBLE PRECISION,
  curation_score DOUBLE PRECISION,
   clip_aesthetic_score DOUBLE PRECISION,
   aesthetic_score DOUBLE PRECISION,
   keep_score DOUBLE PRECISION,
   llm_aesthetic_score DOUBLE PRECISION,
   llm_wall_art_score DOUBLE PRECISION,
   clip_model_version TEXT,
  advanced_metadata_updated_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS file_descriptions (
  file_id BIGINT PRIMARY KEY REFERENCES files(id) ON DELETE CASCADE,
  model_name TEXT NOT NULL,
  description_text TEXT,
  description_json JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS llm_runs (
  id BIGSERIAL PRIMARY KEY,
  provider TEXT NOT NULL DEFAULT 'lmstudio',
  endpoint TEXT,
  vision_model_name TEXT NOT NULL,
  embedding_model_name TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  prompt_text TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS file_llm_results (
  file_id BIGINT PRIMARY KEY REFERENCES files(id) ON DELETE CASCADE,
  llm_run_id BIGINT REFERENCES llm_runs(id) ON DELETE SET NULL,
  prompt_version TEXT NOT NULL,
  vision_model_name TEXT NOT NULL,
  embedding_model_name TEXT NOT NULL,
  description_text TEXT NOT NULL,
  tags TEXT[] NOT NULL DEFAULT '{}',
  llm_payload_json JSONB,
  aesthetic_score DOUBLE PRECISION,
  wall_art_score DOUBLE PRECISION,
  description_embedding VECTOR(384),
  processed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS file_labels (
  file_id BIGINT PRIMARY KEY REFERENCES files(id) ON DELETE CASCADE,
  favorite_flag BOOLEAN,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_files_taken_at ON files(photo_taken_at);
CREATE INDEX IF NOT EXISTS idx_files_camera_make ON files(camera_make);
CREATE INDEX IF NOT EXISTS idx_files_camera_model ON files(camera_model);

CREATE INDEX IF NOT EXISTS idx_file_descriptions_tsv
ON file_descriptions
USING GIN (to_tsvector('english', COALESCE(description_text, '')));

CREATE INDEX IF NOT EXISTS idx_file_llm_results_tsv
ON file_llm_results
USING GIN (to_tsvector('english', COALESCE(description_text, '')));
CREATE INDEX IF NOT EXISTS idx_file_llm_results_tags_gin
ON file_llm_results USING GIN (tags);
CREATE INDEX IF NOT EXISTS idx_file_llm_results_embedding
ON file_llm_results USING ivfflat (description_embedding vector_cosine_ops)
WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_llm_runs_created_at ON llm_runs(created_at DESC);


ALTER TABLE file_metrics ADD COLUMN IF NOT EXISTS technical_quality_score DOUBLE PRECISION;
ALTER TABLE file_metrics ADD COLUMN IF NOT EXISTS semantic_relevance_score DOUBLE PRECISION;
ALTER TABLE file_metrics ADD COLUMN IF NOT EXISTS curation_score DOUBLE PRECISION;
ALTER TABLE file_metrics ADD COLUMN IF NOT EXISTS clip_aesthetic_score DOUBLE PRECISION;
ALTER TABLE file_metrics ADD COLUMN IF NOT EXISTS aesthetic_score DOUBLE PRECISION;
ALTER TABLE file_metrics ADD COLUMN IF NOT EXISTS keep_score DOUBLE PRECISION;
ALTER TABLE file_metrics ADD COLUMN IF NOT EXISTS llm_aesthetic_score DOUBLE PRECISION;
ALTER TABLE file_metrics ADD COLUMN IF NOT EXISTS llm_wall_art_score DOUBLE PRECISION;
ALTER TABLE file_metrics ADD COLUMN IF NOT EXISTS clip_model_version TEXT;
ALTER TABLE file_metrics ADD COLUMN IF NOT EXISTS advanced_metadata_updated_at TIMESTAMPTZ;

-- Migrate LLM scores from file_llm_results into file_metrics (normalize 0-100 to 0-1)
UPDATE file_metrics fm
SET llm_aesthetic_score = flm.aesthetic_score / 100.0,
    llm_wall_art_score = flm.wall_art_score / 100.0
FROM file_llm_results flm
WHERE fm.file_id = flm.file_id
  AND (fm.llm_aesthetic_score IS NULL OR fm.llm_wall_art_score IS NULL);

-- Remove orphaned columns from old scoring systems (NIMA, print sizing)
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='file_metrics' AND column_name='nima_score') THEN
    ALTER TABLE file_metrics DROP COLUMN nima_score;
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='file_metrics' AND column_name='print_score_6x8') THEN
    ALTER TABLE file_metrics DROP COLUMN print_score_6x8;
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='file_metrics' AND column_name='print_score_8x10') THEN
    ALTER TABLE file_metrics DROP COLUMN print_score_8x10;
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='file_metrics' AND column_name='print_score_12x18') THEN
    ALTER TABLE file_metrics DROP COLUMN print_score_12x18;
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_file_metrics_curation_score ON file_metrics(curation_score);
CREATE INDEX IF NOT EXISTS idx_file_metrics_clip_aesthetic_score ON file_metrics(clip_aesthetic_score);
CREATE INDEX IF NOT EXISTS idx_file_metrics_aesthetic_score ON file_metrics(aesthetic_score);
CREATE INDEX IF NOT EXISTS idx_file_metrics_keep_score ON file_metrics(keep_score);
CREATE INDEX IF NOT EXISTS idx_file_metrics_llm_aesthetic_score ON file_metrics(llm_aesthetic_score);
CREATE INDEX IF NOT EXISTS idx_file_metrics_llm_wall_art_score ON file_metrics(llm_wall_art_score);


CREATE INDEX IF NOT EXISTS idx_file_labels_favorite_flag ON file_labels (favorite_flag);

-- Pipeline run tracking tables (added for continuous improvement observability)
CREATE TABLE IF NOT EXISTS pipeline_runs (
  id BIGSERIAL PRIMARY KEY,
  run_id TEXT NOT NULL DEFAULT gen_random_uuid()::TEXT,
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ,
  status TEXT NOT NULL DEFAULT 'running',
   clip_model_version TEXT,
   description_provider TEXT,
   description_model_name TEXT,
   ingest_limit INTEGER,
   ingest_strategy TEXT,
   total_files_ingested INTEGER DEFAULT 0,
   total_metrics_scored INTEGER DEFAULT 0,
   total_clip_aesthetic_scored INTEGER DEFAULT 0,
   total_described INTEGER DEFAULT 0,
   total_skipped INTEGER DEFAULT 0,
   total_failed INTEGER DEFAULT 0,
   blur_min DOUBLE PRECISION,
   blur_max DOUBLE PRECISION,
   blur_median DOUBLE PRECISION,
   blur_p25 DOUBLE PRECISION,
   blur_p75 DOUBLE PRECISION,
   blur_p90 DOUBLE PRECISION,
   blur_stddev DOUBLE PRECISION,
   brightness_min DOUBLE PRECISION,
   brightness_max DOUBLE PRECISION,
   brightness_median DOUBLE PRECISION,
   brightness_p25 DOUBLE PRECISION,
   brightness_p75 DOUBLE PRECISION,
   brightness_p90 DOUBLE PRECISION,
   brightness_stddev DOUBLE PRECISION,
   contrast_min DOUBLE PRECISION,
   contrast_max DOUBLE PRECISION,
   contrast_median DOUBLE PRECISION,
   contrast_p25 DOUBLE PRECISION,
   contrast_p75 DOUBLE PRECISION,
   contrast_p90 DOUBLE PRECISION,
   contrast_stddev DOUBLE PRECISION,
   entropy_min DOUBLE PRECISION,
   entropy_max DOUBLE PRECISION,
   entropy_median DOUBLE PRECISION,
   entropy_p25 DOUBLE PRECISION,
   entropy_p75 DOUBLE PRECISION,
   entropy_p90 DOUBLE PRECISION,
   entropy_stddev DOUBLE PRECISION,
   noise_min DOUBLE PRECISION,
   noise_max DOUBLE PRECISION,
   noise_median DOUBLE PRECISION,
   noise_p25 DOUBLE PRECISION,
   noise_p75 DOUBLE PRECISION,
   noise_p90 DOUBLE PRECISION,
   noise_stddev DOUBLE PRECISION,
   technical_quality_min DOUBLE PRECISION,
   technical_quality_max DOUBLE PRECISION,
   technical_quality_median DOUBLE PRECISION,
   technical_quality_p25 DOUBLE PRECISION,
   technical_quality_p75 DOUBLE PRECISION,
   technical_quality_p90 DOUBLE PRECISION,
   technical_quality_stddev DOUBLE PRECISION,
   clip_aesthetic_min DOUBLE PRECISION,
   clip_aesthetic_max DOUBLE PRECISION,
   clip_aesthetic_median DOUBLE PRECISION,
   clip_aesthetic_p25 DOUBLE PRECISION,
   clip_aesthetic_p75 DOUBLE PRECISION,
   clip_aesthetic_p90 DOUBLE PRECISION,
   clip_aesthetic_stddev DOUBLE PRECISION,
   aesthetic_min DOUBLE PRECISION,
   aesthetic_max DOUBLE PRECISION,
   aesthetic_median DOUBLE PRECISION,
   aesthetic_p25 DOUBLE PRECISION,
   aesthetic_p75 DOUBLE PRECISION,
   aesthetic_p90 DOUBLE PRECISION,
   aesthetic_stddev DOUBLE PRECISION,
   keep_min DOUBLE PRECISION,
   keep_max DOUBLE PRECISION,
   keep_median DOUBLE PRECISION,
   keep_p25 DOUBLE PRECISION,
   keep_p75 DOUBLE PRECISION,
   keep_p90 DOUBLE PRECISION,
   keep_stddev DOUBLE PRECISION,
   curation_min DOUBLE PRECISION,
   curation_max DOUBLE PRECISION,
   curation_median DOUBLE PRECISION,
   curation_p25 DOUBLE PRECISION,
   curation_p75 DOUBLE PRECISION,
   curation_p90 DOUBLE PRECISION,
   curation_stddev DOUBLE PRECISION,
   semantic_relevance_min DOUBLE PRECISION,
   semantic_relevance_max DOUBLE PRECISION,
   semantic_relevance_median DOUBLE PRECISION,
   semantic_relevance_p25 DOUBLE PRECISION,
   semantic_relevance_p75 DOUBLE PRECISION,
   semantic_relevance_p90 DOUBLE PRECISION,
   semantic_relevance_stddev DOUBLE PRECISION,
   notes TEXT
);

ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS clip_model_version TEXT;
ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS description_provider TEXT;
ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS description_model_name TEXT;
ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS ingest_limit INTEGER;
ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS ingest_strategy TEXT;
ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS total_files_ingested INTEGER DEFAULT 0;
ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS total_metrics_scored INTEGER DEFAULT 0;
ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS total_clip_aesthetic_scored INTEGER DEFAULT 0;
ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS total_described INTEGER DEFAULT 0;
ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS total_skipped INTEGER DEFAULT 0;
ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS total_failed INTEGER DEFAULT 0;
ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS notes TEXT;

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_started_at ON pipeline_runs(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status ON pipeline_runs(status);
CREATE UNIQUE INDEX IF NOT EXISTS idx_pipeline_runs_run_id ON pipeline_runs(run_id);
