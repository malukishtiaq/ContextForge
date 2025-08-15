from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from openai import OpenAI

from app.core.config import settings
from app.services.reranker.llm_score import LLMReranker
import re


@dataclass
class Answer:
    text: str
    citations: list[dict]
    snippets: list[dict] | None
    confidence: float


def _enhance_citations(text: str, chunks: list[dict]) -> str:
    """Enhance text with citations for sentences that don't have them."""
    if not chunks:
        return text
    
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    enhanced_sentences = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # Check if sentence already has a citation
        if "[page" in sentence:
            enhanced_sentences.append(sentence)
            continue
        
        # Find the best matching chunk for this sentence
        best_chunk = None
        best_score = 0.0
        
        for chunk in chunks:
            chunk_text = chunk.get("text", "")
            # Simple word overlap scoring
            sentence_words = set(sentence.lower().split())
            chunk_words = set(chunk_text.lower().split())
            if sentence_words and chunk_words:
                overlap = len(sentence_words & chunk_words) / len(sentence_words)
                if overlap > best_score:
                    best_score = overlap
                    best_chunk = chunk
        
        # Add citation if we found a good match
        if best_chunk and best_score > 0.1:  # Threshold for relevance
            page = best_chunk.get("page")
            if page is not None:
                enhanced_sentences.append(f"{sentence} [page {page}]")
            else:
                enhanced_sentences.append(sentence)
        else:
            enhanced_sentences.append(sentence)
    
    return " ".join(enhanced_sentences)


def _extract_snippets(text: str, chunks: list[dict]) -> list[dict]:
    """
    Extract exact text snippets that support the answer.
    
    Args:
        text: Generated answer text
        chunks: Source chunks used for the answer
        
    Returns:
        List of snippets with page and text
    """
    snippets = []
    
    for chunk in chunks:
        chunk_text = chunk.get("text", "")
        page = chunk.get("page_start") or chunk.get("page")
        
        # Find sentences in the answer that are supported by this chunk
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check if this sentence is supported by the chunk
            sentence_words = set(sentence.lower().split())
            chunk_words = set(chunk_text.lower().split())
            
            if sentence_words and chunk_words:
                overlap = len(sentence_words & chunk_words) / len(sentence_words)
                if overlap > 0.3:  # Higher threshold for snippet relevance
                    snippets.append({
                        "page": page,
                        "text": sentence,
                        "relevance": overlap
                    })
    
    # Remove duplicates and sort by relevance
    unique_snippets = []
    seen_sentences = set()
    
    for snippet in sorted(snippets, key=lambda x: x["relevance"], reverse=True):
        sentence_key = snippet["text"].lower().strip()
        if sentence_key not in seen_sentences:
            unique_snippets.append({
                "page": snippet["page"],
                "text": snippet["text"]
            })
            seen_sentences.add(sentence_key)
    
    return unique_snippets[:5]  # Limit to top 5 snippets


def generate_answer(
    question: str,
    system_prompt: str,
    context: str,
    top_chunks: list[dict],
    quote_mode: bool,
) -> Answer:
    client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    user = f"Question: {question}\n\nContext:\n{context}"
    resp = client.chat.completions.create(
        model=settings.chat_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user},
        ],
        temperature=0,
    )
    text = resp.choices[0].message.content or ""

    # Citation enhancement: ensure citations for sentences without them
    text = _enhance_citations(text, top_chunks)

    citations = [{"page": c.get("page"), "chunk_id": c.get("chunk_id")} for c in top_chunks]
    confidence = 0.0
    return Answer(text=text, citations=citations, snippets=None, confidence=confidence)


