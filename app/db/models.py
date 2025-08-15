from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Index
from sqlmodel import Field, SQLModel


class Document(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    bytes: int
    pages: Optional[int] = None
    chunks: Optional[int] = None
    sha256: str
    status: str = Field(default="queued")
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (
        Index("ix_document_sha256_name", "sha256", "name"),
    )

