# API Contract (v1)

Base path: `/api/v1`

## Endpoints
- `GET /health`
- `GET /photos`
- `GET /photos/:id`
- `PATCH /photos/:id/labels`
- `GET /photos/:id/image?size=thumb|full`
- `GET /facets`

## Stub mode
Set `STUB_MODE=true` in server env to return deterministic mock responses.
This enables UI development even before running ingestion.
