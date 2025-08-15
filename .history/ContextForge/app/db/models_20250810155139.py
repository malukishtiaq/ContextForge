from datetime import datetime
from typing import Literal, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Document(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    bytes: int
    pages: Optional[int] = None
    chunks: Optional[int] = None
    sha256: str
    status: Literal["queued", "processing", "ready", "failed"] = "queued"
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

