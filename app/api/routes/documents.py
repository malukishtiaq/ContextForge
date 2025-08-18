from __future__ import annotations

import hashlib
import os
from typing import Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from fastapi import status as http_status

from app.api.schemas.documents import CreateDocumentResponse, DocumentOut
from app.core.config import settings
from app.db import repo
from app.db.models import Document
from app.deps import blob_path, chunks_path, get_redis_queue, get_vectorstore, parsed_path

router = APIRouter(prefix="/v1/documents", tags=["documents"])


async def _download(url: str) -> bytes:
    """Download document from URL with enhanced error handling."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(url)
            r.raise_for_status()
            
            # Check content type
            content_type = r.headers.get("content-type", "").lower()
            if not content_type.startswith("application/pdf"):
                raise HTTPException(
                    http_status.HTTP_400_BAD_REQUEST, 
                    f"URL must point to a PDF file, got: {content_type}"
                )
            
            # Check file size (limit to 100MB)
            content_length = r.headers.get("content-length")
            if content_length and int(content_length) > 100 * 1024 * 1024:
                raise HTTPException(
                    http_status.HTTP_400_BAD_REQUEST,
                    "File too large (max 100MB)"
                )
            
            return r.content
            
    except httpx.TimeoutException:
        raise HTTPException(
            http_status.HTTP_408_REQUEST_TIMEOUT,
            "Download timeout - URL may be slow or unavailable"
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                http_status.HTTP_400_BAD_REQUEST,
                "URL not found - check if the document exists"
            )
        elif e.response.status_code >= 500:
            raise HTTPException(
                http_status.HTTP_502_BAD_GATEWAY,
                "Remote server error - try again later"
            )
        else:
            raise HTTPException(
                http_status.HTTP_400_BAD_REQUEST,
                f"Download failed with status {e.response.status_code}"
            )
    except Exception as e:
        raise HTTPException(
            http_status.HTTP_400_BAD_REQUEST,
            f"Download failed: {str(e)}"
        )


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@router.post("", response_model=CreateDocumentResponse)
async def create_document(
    background: BackgroundTasks,
    file: Optional[UploadFile] = File(default=None),
    url: Optional[str] = None,
):
    if file is None and not url:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST, "Provide file or url")

    content: bytes
    name: str
    if url:
        content = await _download(url)
        name = url.split("/")[-1] or "document.pdf"
    else:
        name = file.filename or "document.pdf"
        content = await file.read()

    if not content:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST, "Empty document")

    sha = _sha256_bytes(content)
    doc: Document = repo.create_document(name=name, sha256=sha, bytes=len(content))

    # Save blob
    blob = blob_path(str(doc.id))
    with open(blob, "wb") as f:
        f.write(content)

    # Enqueue ingest job
    q = get_redis_queue()
    q.enqueue("app.workers.jobs.ingest", str(doc.id))

    return CreateDocumentResponse(docId=doc.id, status=doc.status)


@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: UUID):
    doc = repo.get_document(doc_id)
    if doc is None:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, "Not found")
    return DocumentOut.model_validate(doc)


@router.get("", response_model=list[DocumentOut])
def list_documents(limit: int = Query(default=50, le=200), status: Optional[str] = None):
    docs = repo.list_documents(limit=limit, status=status)
    return [DocumentOut.model_validate(d) for d in docs]


@router.delete("/{doc_id}")
def delete_document(doc_id: UUID) -> dict:
    doc = repo.get_document(doc_id)
    if doc is None:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, "Not found")

    # purge vector namespace
    vs = get_vectorstore()
    namespace = sanitize_namespace(doc_id)
    vs.delete_namespace(namespace)

    # remove files
    for p in [blob_path(str(doc_id)), parsed_path(str(doc_id)), chunks_path(str(doc_id))]:
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass

    repo.delete_document(doc_id)
    return {"status": "deleted"}


