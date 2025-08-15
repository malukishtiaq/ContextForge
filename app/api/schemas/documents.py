from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentOut(BaseModel):
    id: UUID
    name: str
    bytes: int
    pages: Optional[int] = None
    chunks: Optional[int] = None
    sha256: str
    status: str
    error: Optional[str] = None
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    class Config:
        from_attributes = True
        populate_by_name = True


class CreateDocumentResponse(BaseModel):
    docId: UUID
    status: str


