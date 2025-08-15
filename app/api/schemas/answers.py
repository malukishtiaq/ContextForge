from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel


class AnswerRequest(BaseModel):
    question: str
    docIds: list[UUID]
    topK: Optional[int] = None
    quoteMode: bool = False


class Citation(BaseModel):
    page: int
    chunkId: str


class Snippet(BaseModel):
    page: int
    text: str


class AnswerResponse(BaseModel):
    answer: str
    citations: list[Citation]
    snippets: Optional[list[Snippet]] = None
    confidence: float
    metrics: dict[str, Any]


