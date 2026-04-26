# API Contract (v1) — updated 2026-04-26

Base path: `/api/v1`

## Endpoints

- `GET /health` — DB health + pipeline run info + file stats
- `GET /photos?sort=aesthetic_desc&page=1&pageSize=40&q=search+term` — paginated photo list
- `GET /photos/:id` — single photo detail with full metrics
- `PATCH /photos/:id/labels` — update favorite flag and/or notes
- `GET /photos/:id/image?size=thumb|full&downloadName=name.jpg` — serve image or thumbnail
- `GET /facets` — camera, category, status, and date range facets

## Score scales in API responses

All scores are returned as `number | null`. The scale depends on the field:

### 0–1 scale (decimal)
| Field | Source table/column | Description |
|-------|-------------------|-------------|
| `aestheticScore` | `file_metrics.aesthetic_score` | CLIP-derived aesthetic score |
| `curationScore` | `file_metrics.curation_score` | Final rank score |
| `blurScore` | `file_metrics.blur_score` | Blur level (higher = more blur) |
| `brightnessScore` | `file_metrics.brightness_score` | Brightness level |
| `contrastScore` | `file_metrics.contrast_score` | Contrast level |
| `entropyScore` | `file_metrics.entropy_score` | Detail richness |
| `noiseScore` | `file_metrics.noise_score` | Noise level |
| `technicalQualityScore` | `file_metrics.technical_quality_score` | Pure image quality |
| `semanticRelevanceScore` | `file_metrics.semantic_relevance_score` | Semantic context signal |

### 0–100 scale (percentage)
| Field | Source table/column | Description |
|-------|-------------------|-------------|
| `wallArtScore` | `file_metrics.llm_wall_art_score * 100` | LLM wall art suitability |

## Sort options for `/photos?sort=`

- `aesthetic_desc` (default) — by aesthetic score descending
- `curation_desc` — by curation score descending
- `sharpness_desc` — less blur first
- `exposure_desc` — brighter first
- `contrast_desc` — higher contrast first
- `noise_asc` — cleaner photos first
- `date_desc` / `date_asc` — by photo timestamp
- `random` — shuffled results

## Stub mode

Set `STUB_MODE=true` in server env to return deterministic mock responses for all endpoints. This enables UI development without running ingestion.
