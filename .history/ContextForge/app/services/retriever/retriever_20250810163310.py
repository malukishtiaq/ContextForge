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


def _bm25_score(query: str, text: str, avg_doc_length: float, doc_length: int, 
                doc_freq: dict, total_docs: int, k1: float = 1.2, b: float = 0.75) -> float:
    """
    Calculate BM25 score for a document chunk.
    
    Args:
        query: Search query
        text: Document text
        avg_doc_length: Average document length in the collection
        doc_length: Current document length
        doc_freq: Document frequency for each term
        total_docs: Total number of documents
        k1: BM25 parameter (default: 1.2)
        b: BM25 parameter (default: 0.75)
    
    Returns:
        BM25 score
    """
    query_terms = re.findall(r'\b\w+\b', query.lower())
    text_terms = re.findall(r'\b\w+\b', text.lower())
    
    if not query_terms or not text_terms:
        return 0.0
    
    score = 0.0
    for term in query_terms:
        if term in text_terms:
            # Term frequency in document
            tf = text_terms.count(term)
            
            # Inverse document frequency
            df = doc_freq.get(term, 0)
            if df == 0:
                continue
            idf = math.log((total_docs - df + 0.5) / (df + 0.5))
            
            # BM25 formula
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * (doc_length / avg_doc_length))
            
            score += idf * (numerator / denominator)
    
    return score


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
        # Vector search
        qvec = self.embedder.embed_query(query)
        raw = self.vectorstore.search(namespace=namespace, query_vector=qvec, k=k)
        
        # Convert to chunks
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
        vector_scores = [float(r["score"]) for r in raw]
        
        # BM25 scoring (hybrid approach)
        if settings.enable_bm25 and chunks:
            # Calculate document statistics for BM25
            doc_lengths = [len(chunk["text"].split()) for chunk in chunks]
            avg_doc_length = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 0
            
            # Calculate document frequency for terms in the collection
            all_texts = [chunk["text"] for chunk in chunks]
            doc_freq = {}
            for text in all_texts:
                terms = set(re.findall(r'\b\w+\b', text.lower()))
                for term in terms:
                    doc_freq[term] = doc_freq.get(term, 0) + 1
            
            # Calculate BM25 scores
            bm25_scores = []
            for chunk, doc_len in zip(chunks, doc_lengths):
                bm25_score = _bm25_score(
                    query, chunk["text"], avg_doc_length, doc_len, 
                    doc_freq, len(chunks)
                )
                bm25_scores.append(bm25_score)
            
            # Normalize BM25 scores to 0-1 range
            if bm25_scores:
                max_bm25 = max(bm25_scores)
                if max_bm25 > 0:
                    bm25_scores = [score / max_bm25 for score in bm25_scores]
            
            # Hybrid scoring: combine vector and BM25 (configurable weights)
            hybrid_scores = []
            for vs, bs in zip(vector_scores, bm25_scores):
                hybrid_score = (settings.vector_weight * vs + 
                              settings.bm25_weight * bs)
                hybrid_scores.append(hybrid_score)
            
            scores = hybrid_scores
        else:
            scores = vector_scores
        
        # Dedupe near-identical chunks
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


