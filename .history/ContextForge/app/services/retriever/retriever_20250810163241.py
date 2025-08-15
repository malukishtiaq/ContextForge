from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import math
import re

from app.core.config import settings
from app.services.embeddings.base import Embedder
from app.services.vectorstore.base import VectorStore


def _jaccard(a: str, b: str) -> float:
    sa = set(a.split())
    sb = set(b.split())
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / max(1, len(sa | sb))


@dataclass
class Hit:
    chunk: dict
    score: float


@dataclass
class RetrievalResult:
    hits: List[Hit]
    metrics: dict


class Retriever:
    def __init__(self, embedder: Embedder, vectorstore: VectorStore) -> None:
        self.embedder = embedder
        self.vectorstore = vectorstore

    def search(self, query: str, namespace: str, k: int, k_final: int) -> RetrievalResult:
        qvec = self.embedder.embed_query(query)
        raw = self.vectorstore.search(namespace=namespace, query_vector=qvec, k=k)
        # convert to chunks
        chunks = [
            {
                "chunk_id": r["payload"].get("chunk_id"),
                "text": r["payload"].get("text", ""),
                "page_start": r["payload"].get("page_start"),
                "page_end": r["payload"].get("page_end"),
                "section": r["payload"].get("section"),
            }
            for r in raw
        ]
        scores = [float(r["score"]) for r in raw]
        # dedupe near-identical
        deduped: list[tuple[dict, float]] = []
        for c, s in zip(chunks, scores):
            if not any(_jaccard(c["text"], d[0]["text"]) > 0.95 for d in deduped):
                deduped.append((c, s))

        deduped = deduped[:k_final]
        hits = [Hit(chunk=c, score=s) for c, s in deduped]
        max_sim = max(scores) if scores else 0.0
        avg_top3 = sum(scores[:3]) / min(3, len(scores)) if scores else 0.0
        metrics = {"maxSim": max_sim, "avgTop3": avg_top3, "k": len(hits)}
        return RetrievalResult(hits=hits, metrics=metrics)


