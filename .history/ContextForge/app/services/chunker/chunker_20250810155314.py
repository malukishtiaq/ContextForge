from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

import tiktoken

from app.core.config import settings
from app.services.parser.base import ParsedPage


_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass
class Chunk:
    id: str
    doc_id: str
    page_start: int
    page_end: int
    section: str | None
    type: Literal["text", "table", "caption"]
    text: str


def _num_tokens(text: str) -> int:
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def _pack_sentences(sentences: list[str], target: int, overlap: int) -> list[str]:
    enc = tiktoken.get_encoding("cl100k_base")
    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0
    for s in sentences:
        s_tokens = len(enc.encode(s))
        if current and current_tokens + s_tokens > target:
            chunks.append(" ".join(current).strip())
            # make overlap
            if overlap > 0 and chunks[-1]:
                overlap_sents = enc.encode(chunks[-1])
                # naive overlap by tokens approximated with last sentence
                if current:
                    current = [current[-1]]
                    current_tokens = len(enc.encode(current[0]))
                else:
                    current = []
                    current_tokens = 0
        current.append(s)
        current_tokens += s_tokens
    if current:
        chunks.append(" ".join(current).strip())
    return [c for c in chunks if c]


def chunk_pages(doc_id: str, pages: list[ParsedPage]) -> tuple[list[Chunk], dict]:
    target = settings.chunk_target_tokens
    overlap = settings.chunk_overlap_tokens
    chunks: list[Chunk] = []
    for page in pages:
        text = page["text"]
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        sentences = []
        for p in paragraphs:
            sentences.extend(_SENTENCE_SPLIT_RE.split(p))
        if not sentences:
            sentences = [text]
        packed = _pack_sentences(sentences, target=target, overlap=overlap)
        for idx, ctext in enumerate(packed):
            chunks.append(
                Chunk(
                    id=f"{doc_id}:{page['page']}:{idx}",
                    doc_id=doc_id,
                    page_start=page["page"],
                    page_end=page["page"],
                    section=None,
                    type="text",
                    text=ctext,
                )
            )
    stats = {"chunks": len(chunks)}
    return chunks, stats


