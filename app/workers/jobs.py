from __future__ import annotations

import json

from app.core.config import settings
from app.deps import blob_path, chunks_path, get_embedder, get_vectorstore, parsed_path, sanitize_namespace
from app.db import repo
from app.services.chunker.chunker import chunk_pages
from app.services.parser.pdf_pymupdf import parse_pdf_pymupdf


def ingest(doc_id: str) -> None:
    # update status processing
    from uuid import UUID

    try:
        repo.update_status(UUID(doc_id), status="processing")
        pdf = blob_path(doc_id)
        pages, meta = parse_pdf_pymupdf(pdf)
        with open(parsed_path(doc_id), "w", encoding="utf-8") as f:
            json.dump({"pages": pages, "meta": meta}, f)

        chunks, stats = chunk_pages(doc_id, pages)
        with open(chunks_path(doc_id), "w", encoding="utf-8") as f:
            json.dump({"chunks": [c.__dict__ for c in chunks], "stats": stats}, f)

        embedder = get_embedder()
        vectors = embedder.embed_texts([c.text for c in chunks])
        vs = get_vectorstore()
        payloads = []
        for c, vec in zip(chunks, vectors):
            payloads.append(
                {
                    "id": c.id,
                    "vector": vec,
                    "payload": {
                        "text": c.text,
                        "page_start": c.page_start,
                        "page_end": c.page_end,
                        "section": c.section,
                        "chunk_id": c.id,
                    },
                }
            )
        namespace = sanitize_namespace(doc_id)
        vs.upsert(namespace=namespace, vectors=payloads)

        repo.update_status(
            UUID(doc_id), status="ready", pages=meta.get("total_pages"), chunks=len(chunks)
        )
    except Exception as e:  # pragma: no cover - tested via route monkeypatches
        repo.update_status(UUID(doc_id), status="failed", error=str(e))


