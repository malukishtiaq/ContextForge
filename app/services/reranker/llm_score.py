from __future__ import annotations

from typing import List

from openai import OpenAI

from app.core.config import settings


class LLMReranker:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)

    def score(self, question: str, snippets: list[str]) -> list[float]:  # pragma: no cover - optional
        prompt = (
            "Score 0–5 how well the snippet answers the question. Reply with a number only.\n"
            f"Question: {question}\n"
            "Snippet: {snippet}"
        )
        scores: list[float] = []
        for snippet in snippets:
            resp = self.client.chat.completions.create(
                model=settings.chat_model,
                messages=[{"role": "user", "content": prompt.format(snippet=snippet)}],
                temperature=0,
            )
            try:
                val = float(resp.choices[0].message.content.strip())
            except Exception:
                val = 0.0
            scores.append(val)
        return scores


