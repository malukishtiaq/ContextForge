from __future__ import annotations

import time
from typing import List

from openai import OpenAI


class OpenAIEmbedder:
    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self.model = model
        self._client = OpenAI(api_key=api_key, base_url=base_url)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        batch = 256
        for i in range(0, len(texts), batch):
            chunk = texts[i : i + batch]
            vectors.extend(self._embed_with_retry(chunk))
        return vectors

    def embed_query(self, text: str) -> list[float]:
        return self._embed_with_retry([text])[0]

    def _embed_with_retry(self, inputs: list[str]) -> list[list[float]]:
        delay = 1.0
        for attempt in range(6):
            try:
                resp = self._client.embeddings.create(model=self.model, input=inputs)
                return [d.embedding for d in resp.data]
            except Exception:  # pragma: no cover - network errors
                if attempt == 5:
                    raise
                time.sleep(delay)
                delay *= 2


