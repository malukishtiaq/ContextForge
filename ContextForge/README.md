# ContextForge

Production-ready RAG core (FastAPI + Qdrant + Redis/RQ). Ingest PDFs, chunk, embed, index, and answer with citations.

## Quickstart

1. Copy env and start services
   ```bash
   cp .env.sample .env
   docker compose up -d
   ```
2. Create venv and install
   ```bash
   make venv
   ```
3. Run API
   ```bash
   make run
   ```
4. Start worker (separate terminal)
   ```bash
   make worker
   ```
5. Use API
   - GET `/v1/health`
   - POST `/v1/documents` (multipart `file`)
   - GET `/v1/documents/{id}`
   - POST `/v1/answers`

## Structure
See `app/` for modules, `workers/` for RQ worker, `tests/` for coverage.

## Development
- `make fmt` formatters
- `make test` run tests
# ContextForge
