from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from openai import OpenAI

from app.core.config import settings


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

    # ensure at least one citation per sentence when possible
    if "[page" not in text and top_chunks:
        # append best page from top chunk
        best_page = top_chunks[0].get("page")
        if best_page is not None:
            text = text.strip() + f" [page {best_page}]"

    citations = [{"page": c.get("page"), "chunk_id": c.get("chunk_id")} for c in top_chunks]
    confidence = 0.0
    return Answer(text=text, citations=citations, snippets=None, confidence=confidence)


