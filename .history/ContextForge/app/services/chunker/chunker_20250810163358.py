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


def _detect_content_type(text: str) -> Literal["text", "table", "caption"]:
    """
    Detect the type of content in a text chunk.
    
    Args:
        text: Text content to analyze
        
    Returns:
        Content type: "text", "table", or "caption"
    """
    # Detect tables by common patterns
    table_patterns = [
        r'\|\s*[^|]+\s*\|',  # Pipe-separated columns
        r'\+[-=]+\+',         # ASCII table borders
        r'\t+',               # Tab-separated
        r'\s{3,}',            # Multiple spaces (aligned columns)
    ]
    
    for pattern in table_patterns:
        if re.search(pattern, text):
            return "table"
    
    # Detect captions (short text, often ending with numbers or special chars)
    if len(text.split()) <= 10 and re.search(r'[0-9]+$', text.strip()):
        return "caption"
    
    # Default to text
    return "text"


def _smart_chunk_text(text: str, target_tokens: int, overlap_tokens: int) -> list[str]:
    """
    Smart chunking that preserves table structure and captions.
    
    Args:
        text: Text to chunk
        target_tokens: Target token count per chunk
        overlap_tokens: Overlap token count
        
    Returns:
        List of text chunks
    """
    enc = tiktoken.get_encoding("cl100k_base")
    
    # Split by paragraphs first
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    
    chunks = []
    current_chunk = []
    current_tokens = 0
    
    for paragraph in paragraphs:
        # Check if this paragraph is a table
        if _detect_content_type(paragraph) == "table":
            # Don't split tables - keep them as one chunk
            table_tokens = len(enc.encode(paragraph))
            
            # If adding this table would exceed target, finalize current chunk
            if current_chunk and current_tokens + table_tokens > target_tokens:
                chunks.append(" ".join(current_chunk).strip())
                current_chunk = []
                current_tokens = 0
            
            # Add the entire table
            current_chunk.append(paragraph)
            current_tokens += table_tokens
            
            # Finalize chunk after table (tables are natural break points)
            if current_chunk:
                chunks.append(" ".join(current_chunk).strip())
                current_chunk = []
                current_tokens = 0
        else:
            # Regular text - split by sentences
            sentences = _SENTENCE_SPLIT_RE.split(paragraph)
            
            for sentence in sentences:
                sentence_tokens = len(enc.encode(sentence))
                
                # Check if adding this sentence would exceed target
                if current_chunk and current_tokens + sentence_tokens > target_tokens:
                    chunks.append(" ".join(current_chunk).strip())
                    
                    # Create overlap with last sentence
                    if overlap_tokens > 0 and current_chunk:
                        overlap_text = current_chunk[-1]
                        overlap_tokens_actual = len(enc.encode(overlap_text))
                        if overlap_tokens_actual <= overlap_tokens:
                            current_chunk = [overlap_text]
                            current_tokens = overlap_tokens_actual
                        else:
                            current_chunk = []
                            current_tokens = 0
                    else:
                        current_chunk = []
                        current_tokens = 0
                
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
    
    # Add remaining content
    if current_chunk:
        chunks.append(" ".join(current_chunk).strip())
    
    return [c for c in chunks if c.strip()]


def chunk_pages(doc_id: str, pages: list[ParsedPage]) -> tuple[list[Chunk], dict]:
    target = settings.chunk_target_tokens
    overlap = settings.chunk_overlap_tokens
    chunks: list[Chunk] = []
    
    for page in pages:
        text = page["text"]
        
        # Use smart chunking that preserves table structure
        packed = _smart_chunk_text(text, target=target, overlap_tokens=overlap)
        
        for idx, ctext in enumerate(packed):
            # Detect content type for each chunk
            content_type = _detect_content_type(ctext)
            
            chunks.append(
                Chunk(
                    id=f"{doc_id}:{page['page']}:{idx}",
                    doc_id=doc_id,
                    page_start=page["page"],
                    page_end=page["page"],
                    section=None,
                    type=content_type,
                    text=ctext,
                )
            )
    
    # Calculate statistics
    type_counts = {}
    for chunk in chunks:
        chunk_type = chunk.type
        type_counts[chunk_type] = type_counts.get(chunk_type, 0) + 1
    
    stats = {
        "chunks": len(chunks),
        "type_breakdown": type_counts,
        "avg_chunk_tokens": sum(len(tiktoken.get_encoding("cl100k_base").encode(c.text)) for c in chunks) / len(chunks) if chunks else 0
    }
    
    return chunks, stats


