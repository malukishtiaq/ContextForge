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


