from typing import Protocol


class VectorStore(Protocol):
    def upsert(self, namespace: str, vectors: list[dict]) -> None:
        ...

    def search(self, namespace: str, query_vector: list[float], k: int) -> list[dict]:
        ...

    def delete_namespace(self, namespace: str) -> None:
        ...


