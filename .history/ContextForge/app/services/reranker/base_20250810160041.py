from typing import Protocol


class Reranker(Protocol):
    def score(self, question: str, snippets: list[str]) -> list[float]:
        ...


