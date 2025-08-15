from typing import Optional
from uuid import UUID

from sqlmodel import select

from app.db.database import get_session
from app.db.models import Document


def create_document(name: str, sha256: str, bytes: int) -> Document:
    with get_session() as session:
        doc = Document(name=name, sha256=sha256, bytes=bytes, status="queued")
        session.add(doc)
        session.commit()
        session.refresh(doc)
        return doc


def update_status(
    doc_id: UUID,
    status: str,
    pages: Optional[int] = None,
    chunks: Optional[int] = None,
    error: Optional[str] = None,
) -> Document:
    with get_session() as session:
        doc = session.get(Document, doc_id)
        if doc is None:
            raise ValueError("Document not found")
        doc.status = status  # type: ignore
        if pages is not None:
            doc.pages = pages
        if chunks is not None:
            doc.chunks = chunks
        if error is not None:
            doc.error = error
        session.add(doc)
        session.commit()
        session.refresh(doc)
        return doc


def get_document(doc_id: UUID) -> Optional[Document]:
    with get_session() as session:
        return session.get(Document, doc_id)


def list_documents(limit: int = 50, status: Optional[str] = None) -> list[Document]:
    with get_session() as session:
        stmt = select(Document)
        if status:
            stmt = stmt.where(Document.status == status)
        stmt = stmt.order_by(Document.created_at.desc()).limit(limit)
        return list(session.exec(stmt))


def delete_document(doc_id: UUID) -> Optional[Document]:
    with get_session() as session:
        doc = session.get(Document, doc_id)
        if doc is None:
            return None
        session.delete(doc)
        session.commit()
        return doc

