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
  photo_taken_at_source TEXT NOT NULL DEFAULT 'ingest_time',
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
  nima_score DOUBLE PRECISION,
  aesthetic_score DOUBLE PRECISION,
  keep_score DOUBLE PRECISION,
  nima_model_version TEXT,
  advanced_metadata_updated_at TIMESTAMPTZ,
  print_score_6x8 DOUBLE PRECISION,
  print_score_8x10 DOUBLE PRECISION,
  print_score_12x18 DOUBLE PRECISION,
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

CREATE TABLE IF NOT EXISTS file_labels (
  file_id BIGINT PRIMARY KEY REFERENCES files(id) ON DELETE CASCADE,
  keep_flag BOOLEAN,
  reject_flag BOOLEAN,
  favorite_flag BOOLEAN,
  print_candidate_6x8 BOOLEAN,
  print_candidate_8x10 BOOLEAN,
  print_candidate_12x18 BOOLEAN,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_files_taken_at ON files(photo_taken_at);
CREATE INDEX IF NOT EXISTS idx_files_camera_make ON files(camera_make);
CREATE INDEX IF NOT EXISTS idx_files_camera_model ON files(camera_model);
CREATE INDEX IF NOT EXISTS idx_file_metrics_print_12x18 ON file_metrics(print_score_12x18);
CREATE INDEX IF NOT EXISTS idx_file_metrics_print_8x10 ON file_metrics(print_score_8x10);
CREATE INDEX IF NOT EXISTS idx_file_metrics_print_6x8 ON file_metrics(print_score_6x8);
CREATE INDEX IF NOT EXISTS idx_file_metrics_curation_score ON file_metrics(curation_score);

CREATE INDEX IF NOT EXISTS idx_file_descriptions_tsv
ON file_descriptions
USING GIN (to_tsvector('english', COALESCE(description_text, '')));


CREATE INDEX IF NOT EXISTS idx_file_labels_keep_flag ON file_labels (keep_flag);
CREATE INDEX IF NOT EXISTS idx_file_labels_reject_flag ON file_labels (reject_flag);
CREATE INDEX IF NOT EXISTS idx_file_labels_favorite_flag ON file_labels (favorite_flag);

-- Pipeline run tracking tables (added for continuous improvement observability)
CREATE TABLE IF NOT EXISTS pipeline_runs (
  id BIGSERIAL PRIMARY KEY,
  run_id TEXT NOT NULL DEFAULT gen_random_uuid()::TEXT,
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ,
  status TEXT NOT NULL DEFAULT 'running',
  nima_model_version TEXT,
  description_provider TEXT,
  description_model_name TEXT,
  ingest_limit INTEGER,
  ingest_strategy TEXT,
  total_files_ingested INTEGER DEFAULT 0,
  total_metrics_scored INTEGER DEFAULT 0,
  total_nima_scored INTEGER DEFAULT 0,
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
  nima_min DOUBLE PRECISION,
  nima_max DOUBLE PRECISION,
  nima_median DOUBLE PRECISION,
  nima_p25 DOUBLE PRECISION,
  nima_p75 DOUBLE PRECISION,
  nima_p90 DOUBLE PRECISION,
  nima_stddev DOUBLE PRECISION,
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

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_started_at ON pipeline_runs(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status ON pipeline_runs(status);
