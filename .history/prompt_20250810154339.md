perfect — here’s a **copy-paste “Cursor prompt”** you can drop into Cursor to generate a **production-ready Python RAG core**. It’s app-first (FastAPI), runs locally now, deploys later, and stays cleanly **pluggable** for a future Flutter client.

---

# Cursor Prompt — Build a Production RAG Core (Python + FastAPI)

You are building a **production-ready Retrieval-Augmented Generation core service** named **`rag-core`**. It ingests any PDF (small to 1000+ pages), turns it into high-quality chunks with metadata, embeds + indexes them, and answers questions with page-level citations. It must be clean, tested, and modular so a **Flutter app** can call it later over HTTP without changes.

## Tech decisions (lock these in)

* **Language:** Python 3.11+
* **API:** FastAPI + Uvicorn
* **Schemas:** Pydantic v2
* **Storage (local dev):** filesystem under `./data/`
* **Vector DB:** Qdrant (Dockerized local for dev)
* **Embeddings:** OpenAI `text-embedding-3-small` (configurable)
* **LLM for answers:** OpenAI (configurable)
* **Queue/Workers:** RQ + Redis (for large PDF ingest)
* **DB for metadata:** SQLite via SQLModel (documents, statuses, hashes)
* **PDF parsing:** PyMuPDF (`fitz`) for digital text; OCR is a pluggable interface (stub provider for now)
* **Tokenization:** `tiktoken`
* **Optional reranker:** LLM scoring (simple, provider-agnostic) — off by default, toggle via env
* **Logging:** structured logging with Python `logging` + request IDs
* **Tests:** pytest + httpx TestClient
* **Containerization:** Docker + docker-compose (api, worker, redis, qdrant)
* **Style:** black, isort, ruff

## Project layout (create exactly this tree)

```
rag-core/
  pyproject.toml
  requirements.txt
  .env.sample
  Makefile
  docker-compose.yml
  README.md

  data/                # gitignored: blobs, sqlite db
    .gitkeep

  app/
    __init__.py
    main.py
    deps.py
    telemetry.py

    core/
      config.py
      logging.py
      errors.py

    api/
      __init__.py
      routes/
        health.py
        documents.py
        answers.py
      schemas/
        documents.py
        answers.py
        common.py

    db/
      __init__.py
      models.py
      database.py
      repo.py

    services/
      parser/
        __init__.py
        base.py
        pdf_pymupdf.py
        ocr_base.py          # interface only; stub provider
      chunker/
        __init__.py
        chunker.py
      embeddings/
        __init__.py
        base.py
        openai_embedder.py
      vectorstore/
        __init__.py
        base.py
        qdrant_store.py
      retriever/
        __init__.py
        retriever.py
      reranker/
        __init__.py
        base.py
        llm_score.py
      answerer/
        __init__.py
        prompt.py
        answerer.py

    workers/
      __init__.py
      jobs.py
      worker.py

  tests/
    __init__.py
    test_chunker.py
    test_api_documents.py
    test_api_answers.py
```

## Environment & configuration

Create `.env.sample` with:

```
# FastAPI
APP_ENV=dev
APP_HOST=0.0.0.0
APP_PORT=8080
CORS_ORIGINS=*

# Storage
DATA_DIR=./data

# DB (sqlite for metadata)
SQLITE_PATH=./data/meta.db

# Redis/RQ
REDIS_URL=redis://redis:6379/0

# Qdrant
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=

# OpenAI
OPENAI_API_KEY=replace_me
OPENAI_BASE_URL=https://api.openai.com/v1
EMBEDDING_MODEL=text-embedding-3-small
CHAT_MODEL=gpt-4o-mini

# Features
ENABLE_OCR=false
ENABLE_RERANK=false
MAX_CONTEXT_TOKENS=2000
TOP_K=10
TOP_K_FINAL=6
SIM_THRESHOLD_MAX=0.30
SIM_THRESHOLD_AVG=0.26
CHUNK_TARGET_TOKENS=800
CHUNK_OVERLAP_TOKENS=100
```

`core/config.py` must read env via Pydantic `BaseSettings` and expose a singleton `settings`. `core/logging.py` configures JSON logs and injects a `request_id` per request. `telemetry.py` adds middleware for timing and request IDs.

## Database (SQLModel) — minimal but real

`db/models.py`:

* `Document`: `id: UUID`, `name: str`, `bytes: int`, `pages: int|None`, `chunks: int|None`, `sha256: str`, `status: Literal["queued","processing","ready","failed"]`, `error: str|None`, timestamps.
* Index on `(sha256, name)`.

`db/repo.py` exposes:

* `create_document(name, sha256, bytes) -> Document`
* `update_status(doc_id, status, pages=None, chunks=None, error=None)`
* `get_document(doc_id)`
* `list_documents(limit, status?)`
* `delete_document(doc_id)` (also return the blob path to purge)

## Storage (filesystem for dev)

In `deps.py`, expose helpers:

* `blob_path(doc_id) -> str` (PDF)
* `parsed_path(doc_id) -> str` (json of parsed pages)
* `chunks_path(doc_id) -> str` (json of chunks)

## Parser & OCR (pluggable)

`services/parser/base.py` interface:

```python
class ParsedPage(TypedDict):
    page: int
    text: str
    blocks: list[dict]  # optional layout
    lang: str | None

class Parser(Protocol):
    def parse(self, pdf_path: str) -> tuple[list[ParsedPage], dict]: ...
```

`pdf_pymupdf.py` implementation:

* Extract **per page** text (preserve order), try to detect headings by font size if easy, else just text.
* Return pages + meta (`total_pages`).
* If no extractable text and `ENABLE_OCR=true`, call `ocr_base.py` (leave stub; return `NotImplementedError` otherwise).

## Chunker (sentence-aware + overlap)

`services/chunker/chunker.py`:

* Use `tiktoken` to count tokens.
* Split **per page** first, then by paragraphs (`\n\n`) and sentences (regex). Don’t cut tables mid-row (we’ll treat all as text for MVP).
* Target `CHUNK_TARGET_TOKENS` with `CHUNK_OVERLAP_TOKENS`.
  Chunk schema:

```python
@dataclass
class Chunk:
    id: str               # f"{doc_id}:{page}:{idx}"
    doc_id: str
    page_start: int
    page_end:   int
    section:    str | None
    type:       Literal["text","table","caption"]  # use "text" for MVP
    text:       str
```

Return `list[Chunk]` + stats.

## Embeddings (provider interface)

`embeddings/base.py`:

```python
class Embedder(Protocol):
    model: str
    def embed_texts(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...
```

`openai_embedder.py` implements both with batching + retries.

## Vector store (Qdrant)

`vectorstore/base.py`:

```python
class VectorStore(Protocol):
    def upsert(self, namespace: str, vectors: list[dict]): ...
    def search(self, namespace: str, query_vector: list[float], k: int) -> list[dict]: ...
    def delete_namespace(self, namespace: str): ...
```

`qdrant_store.py`:

* Collection name = `namespace` (use `doc:<uuid>`). Distance = cosine. Set payload schema to include `text`, `page_start`, `page_end`, `section`, `chunk_id`.
* Upsert in batches (≤512).
* Search returns hits with score normalized to 0..1 (convert from Qdrant distance).

## Retriever (fusion, dedupe, confidence)

`services/retriever/retriever.py`:

* Steps:

  1. `embed_query(q)`
  2. vector search `k = TOP_K` (only vector for MVP; leave BM25 hook TODO)
  3. **dedupe** near-identical chunks (text Jaccard > 0.95)
  4. keep `TOP_K_FINAL`
  5. compute `maxSim`, `avgTop3`
  6. if below thresholds → **abstain flag**
* Return `hits: list[Hit]` with `{chunk, score}` and `metrics`.

## Reranker (optional)

`reranker/llm_score.py`:

* If `ENABLE_RERANK=true` → call LLM with a small prompt:
  “Score 0–5 how well the snippet answers the question. Reply with a number only.”
* Replace vector order with reranked top 4–6.

## Answerer + prompt

`answerer/prompt.py` provides:

* **System prompt** (strict): “Answer only using the provided context. If missing, say you don’t know. Cite as `[page X]`.”
* Context assembly packs chunks up to `MAX_CONTEXT_TOKENS`. Each chunk includes a header: `[page {page_start}]`.

`answerer/answerer.py`:

* Calls chat model with `{system, user, context}`.
* If model omits citations, append the strongest page ref per sentence from top chunks.
* Output:

```python
@dataclass
class Answer:
    text: str
    citations: list[dict]  # {"page": int, "chunk_id": str}
    snippets: list[dict] | None  # exact spans
    confidence: float
```

## API routes (stable for future Flutter)

`api/routes/health.py`

* `GET /v1/health` → `{status:"ok"}`

`api/routes/documents.py`

* `POST /v1/documents`
  Accepts `multipart/form-data` with `file` (PDF) **or** JSON `{url}` to fetch.
  Flow: compute SHA-256, create DB record (status=queued), save blob, enqueue `workers.jobs.ingest(doc_id)`. Return `{docId, status}`.
* `GET /v1/documents/{doc_id}` → status, pages, chunks, errors.
* `GET /v1/documents` (filters: status, limit)
* `DELETE /v1/documents/{doc_id}` → purge: remove vector namespace, blob, db row.

`api/routes/answers.py`

* `POST /v1/answers`
  Request schema:

  ```json
  {
    "question": "string",
    "docIds": ["uuid"],
    "topK": 10,
    "quoteMode": false
  }
  ```

  For MVP: require exactly one `docId`.
  Flow: retrieve → (optional rerank) → assemble prompt → call LLM → return

  ```json
  {
    "answer": "text with [page X] citations",
    "citations": [{"page": 12, "chunkId": "doc:12:3"}],
    "snippets": [{"page": 12, "text": "…"}],
    "confidence": 0.74,
    "metrics": {"maxSim": 0.41, "avgTop3": 0.36, "k": 6}
  }
  ```

Enable **CORS** (origins from `CORS_ORIGINS`) so a Flutter app can call it later.

## Workers & jobs

`workers/jobs.py`:

* `ingest(doc_id: str)`:

  * update status → `processing`
  * parse PDF → pages.json
  * chunk → chunks.json
  * embed + upsert to Qdrant (`namespace = f"doc:{doc_id}"`)
  * update document stats and set `ready`
  * on exception: set `failed` with `error`

`workers/worker.py`:

* RQ worker that imports `jobs` and listens on queue `"ingest"`.

`deps.py`:

* Provide factories: `get_embedder()`, `get_vectorstore()`, `get_redis_queue()`, `get_db_session()`.

## Error handling

* Central exception handler in `core/errors.py` returning JSON with a `code`, `message`, and `details`.
* Validation errors → 422 with clear messages.
* PDF not parsable → 400 with hint to enable OCR.

## Security (dev-level)

* No auth for local. Structure code so an auth dependency can be added later without changing business logic.

## Token & chunk math

* Use `tiktoken` to compute token lengths precisely.
* Keep context under `MAX_CONTEXT_TOKENS` (default 2000).
* Default chunking: target 800 tokens, 100 overlap.

## Tests

* `test_chunker.py`: verify sentence-aware chunking sizes & overlap.
* `test_api_documents.py`: upload a small PDF, wait for `ready` by calling `jobs.ingest(...)` synchronously (monkeypatch queue), assert DB + files exist.
* `test_api_answers.py`: feed a toy doc with known fact, assert the answer contains the fact and a `[page X]` citation; also test an out-of-scope query returns “don’t have enough information”.

## Tooling & DX

* `Makefile` targets:

  * `make venv` (setup)
  * `make run` (uvicorn hot reload)
  * `make worker` (RQ worker)
  * `make up` (docker compose up)
  * `make down`
  * `make test`
  * `make fmt` (black + isort + ruff)
* `README.md` with quickstart:

  1. `cp .env.sample .env`
  2. `docker compose up -d` (qdrant, redis)
  3. `pip install -r requirements.txt`
  4. `make run` (API on :8080)
  5. `make worker` (start background worker)
  6. Upload a PDF: `POST /v1/documents` (multipart)
  7. Poll `/v1/documents/{id}` until `ready`
  8. Ask: `POST /v1/answers`

## Acceptance criteria (do not skip)

* Uploading a digital PDF triggers ingestion and results in **ready** within seconds/minutes depending on size.
* Answering a question about the PDF returns correct text with **page-level citations**.
* Asking an out-of-scope question returns a conservative “not enough information” response (confidence gating).
* All modules are **interface-driven** (parser, embedder, vectorstore, reranker) so providers can be swapped later.
* The API is **CORS-enabled** and stable for a future Flutter client.

## Implementation notes / details to include

* Normalize Qdrant scores to 0..1 for `maxSim/avgTop3` metrics.
* Chunk IDs = `"{doc_id}:{page}:{idx}"`; `namespace = "doc:{doc_id}"`.
* Use batched embedding (e.g., 256 at a time) with exponential backoff on 429/5xx.
* When composing context, prepend a short header per chunk: `[page {page_start}]`.
* Strict system prompt text (exact):

  ```
  You are a strict PDF QA assistant. Answer ONLY using the provided context.
  If the answer is not in the context, say you don't have enough information.
  Always cite sources as [page X] after the relevant sentence.
  ```
* If the model omits citations, attach the strongest page from the retrieved set per sentence.
* Leave **OCR** as an interface with `ENABLE_OCR=false` default. If enabled later, call provider and preserve page numbers.
* Add `GET /v1/health` and a root `/` that links to `/docs` (FastAPI Swagger).

## Dependencies (requirements.txt)

Pin reasonable versions (or latest stable):

```
fastapi
uvicorn[standard]
pydantic>=2
sqlmodel
python-dotenv
rq
redis
qdrant-client
openai>=1.0.0
numpy
tiktoken
PyMuPDF
httpx
pytest
pytest-asyncio
black
isort
ruff
```

(Keep OCR, reranker heavy libs out for now; we stub their interfaces.)

---

**Generate the full codebase now** following the structure and specs above, with clear docstrings and comments in each module. Ensure the app runs locally via `docker-compose up -d` (for qdrant + redis) and `make run` for the API, with `make worker` to start ingestion workers. Include comprehensive README instructions and passing tests.
