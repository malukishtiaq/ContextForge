from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi import status as http_status

from app.api.schemas.answers import AnswerRequest, AnswerResponse, Citation, Snippet
from app.core.config import settings
from app.services.answerer.answerer import Answer, generate_answer
from app.services.answerer.prompt import build_context, build_system_prompt
from app.services.embeddings.openai_embedder import OpenAIEmbedder
from app.services.retriever.retriever import Retriever
from app.services.vectorstore.qdrant_store import QdrantStore

router = APIRouter(prefix="/v1/answers", tags=["answers"])


@router.post("")
def create_answer(req: AnswerRequest) -> AnswerResponse:
    if not req.docIds or len(req.docIds) != 1:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST, "Provide exactly one docId for MVP")

    embedder = OpenAIEmbedder(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        model=settings.embedding_model,
    )
    vs = QdrantStore(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    retriever = Retriever(embedder=embedder, vectorstore=vs)

    namespace = f"doc:{req.docIds[0]}"
    top_k = req.topK or settings.top_k
    results = retriever.search(req.question, namespace=namespace, k=top_k, k_final=settings.top_k_final)

    # Confidence gating
    if (
        results.metrics.get("maxSim", 0.0) < settings.sim_threshold_max
        or results.metrics.get("avgTop3", 0.0) < settings.sim_threshold_avg
    ):
        abstain_text = "I don't have enough information to answer from the provided document."
        return AnswerResponse(
            answer=abstain_text,
            citations=[],
            snippets=None,
            confidence=0.0,
            metrics=results.metrics,
        )

    # Optional reranking
    if settings.enable_rerank:
        from app.services.reranker.llm_score import LLMReranker
        reranker = LLMReranker()
        chunk_texts = [h.chunk.get("text", "") for h in results.hits]
        scores = reranker.score(req.question, chunk_texts)
        
        # Reorder hits based on reranker scores
        scored_hits = list(zip(results.hits, scores))
        scored_hits.sort(key=lambda x: x[1], reverse=True)
        results.hits = [hit for hit, _ in scored_hits[:settings.top_k_final]]

    context_text, used_chunks = build_context(results.hits, max_tokens=settings.max_context_tokens)
    system_prompt = build_system_prompt()
    answer: Answer = generate_answer(
        question=req.question,
        system_prompt=system_prompt,
        context=context_text,
        top_chunks=used_chunks,
        quote_mode=req.quoteMode,
    )

    return AnswerResponse(
        answer=answer.text,
        citations=[Citation(page=c["page"], chunkId=c["chunk_id"]) for c in answer.citations],
        snippets=[Snippet(page=s["page"], text=s["text"]) for s in (answer.snippets or [])]
        if answer.snippets
        else None,
        confidence=answer.confidence,
        metrics=results.metrics,
    )


