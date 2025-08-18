from __future__ import annotations

from pathlib import Path
from typing import Generator

from redis import Redis
from rq import Queue

from app.core.config import settings
from app.db.database import get_session
from app.services.embeddings.openai_embedder import OpenAIEmbedder
from app.services.vectorstore.qdrant_store import QdrantStore


# ---------- Filesystem paths ----------


def sanitize_namespace(doc_id: str) -> str:
    """Sanitize document ID for use as Qdrant namespace (remove invalid characters)"""
    return f"doc_{doc_id.replace('-', '_')}"


def _ensure_parent(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def blob_path(doc_id: str) -> str:
    return str(_ensure_parent(Path(settings.data_dir) / "blobs" / f"{doc_id}.pdf"))


def parsed_path(doc_id: str) -> str:
    return str(_ensure_parent(Path(settings.data_dir) / "parsed" / f"{doc_id}.pages.json"))


def chunks_path(doc_id: str) -> str:
    return str(_ensure_parent(Path(settings.data_dir) / "chunks" / f"{doc_id}.chunks.json"))


# ---------- Factories ----------


def get_embedder() -> OpenAIEmbedder:
    return OpenAIEmbedder(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        model=settings.embedding_model,
        batch_size=settings.embedding_batch_size,
        max_retries=settings.embedding_max_retries,
    )


def get_vectorstore() -> QdrantStore:
    return QdrantStore(url=settings.qdrant_url, api_key=settings.qdrant_api_key)


def get_redis_queue() -> Queue:
    redis = Redis.from_url(settings.redis_url)
    return Queue("ingest", connection=redis)


def get_db_session() -> Generator:
    return get_session()


