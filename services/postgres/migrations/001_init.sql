CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS photos (
  id BIGSERIAL PRIMARY KEY,
  path TEXT UNIQUE NOT NULL,
  sha256 TEXT NOT NULL,
  mtime TIMESTAMPTZ NOT NULL,
  size_bytes BIGINT NOT NULL,
  width INTEGER,
  height INTEGER,
  exif_datetime TIMESTAMPTZ,
  camera_make TEXT,
  camera_model TEXT,
  lens TEXT,
  iso INTEGER,
  shutter TEXT,
  aperture TEXT,
  focal_length TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS metrics (
  photo_id BIGINT PRIMARY KEY REFERENCES photos(id) ON DELETE CASCADE,
  sharpness DOUBLE PRECISION,
  exposure_clip_hi DOUBLE PRECISION,
  exposure_clip_lo DOUBLE PRECISION,
  contrast DOUBLE PRECISION,
  noise_proxy DOUBLE PRECISION,
  aesthetic_score DOUBLE PRECISION,
  face_count INTEGER,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS embeddings (
  photo_id BIGINT REFERENCES photos(id) ON DELETE CASCADE,
  model_name TEXT NOT NULL,
  embedding vector(512) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (photo_id, model_name)
);

CREATE TABLE IF NOT EXISTS clusters (
  id BIGSERIAL PRIMARY KEY,
  method TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS cluster_members (
  cluster_id BIGINT REFERENCES clusters(id) ON DELETE CASCADE,
  photo_id BIGINT REFERENCES photos(id) ON DELETE CASCADE,
  PRIMARY KEY (cluster_id, photo_id)
);

CREATE TABLE IF NOT EXISTS runs (
  id BIGSERIAL PRIMARY KEY,
  started_at TIMESTAMPTZ DEFAULT now(),
  finished_at TIMESTAMPTZ,
  config_json JSONB
);

CREATE TABLE IF NOT EXISTS selections (
  run_id BIGINT REFERENCES runs(id) ON DELETE CASCADE,
  photo_id BIGINT REFERENCES photos(id) ON DELETE CASCADE,
  rank INTEGER NOT NULL,
  final_score DOUBLE PRECISION NOT NULL,
  PRIMARY KEY (run_id, photo_id)
);

CREATE INDEX IF NOT EXISTS idx_photos_sha256 ON photos(sha256);
CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON embeddings USING ivfflat (embedding vector_cosine_ops);
