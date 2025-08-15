from __future__ import annotations

from typing import List

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm


class QdrantStore:
    def __init__(self, url: str, api_key: str | None) -> None:
        self.client = QdrantClient(url=url, api_key=api_key)

    def _ensure_collection(self, name: str, vector_size: int) -> None:
        collections = self.client.get_collections().collections
        if any(c.name == name for c in collections):
            return
        self.client.recreate_collection(
            collection_name=name,
            vectors_config=qm.VectorParams(size=vector_size, distance=qm.Distance.COSINE),
        )

    def upsert(self, namespace: str, vectors: list[dict]) -> None:
        if not vectors:
            return
        vector_size = len(vectors[0]["vector"])  # derive
        self._ensure_collection(namespace, vector_size)
        points: list[qm.PointStruct] = []
        for v in vectors:
            points.append(
                qm.PointStruct(
                    id=v["id"],
                    vector=v["vector"],
                    payload=v["payload"],
                )
            )
        # batch within 512
        for i in range(0, len(points), 512):
            self.client.upsert(collection_name=namespace, points=points[i : i + 512])

    def search(self, namespace: str, query_vector: list[float], k: int) -> list[dict]:
        hits = self.client.search(collection_name=namespace, query_vector=query_vector, limit=k)
        results = []
        for h in hits:
            # cosine similarity in qdrant returns score in 0..1; treat as similarity directly
            results.append({
                "id": h.id,
                "score": float(h.score),
                "payload": dict(h.payload or {}),
            })
        return results

    def delete_namespace(self, namespace: str) -> None:
        try:
            self.client.delete_collection(collection_name=namespace)
        except Exception:
            pass


