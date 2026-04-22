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

CREATE INDEX IF NOT EXISTS idx_file_descriptions_tsv
ON file_descriptions
USING GIN (to_tsvector('english', COALESCE(description_text, '')));
