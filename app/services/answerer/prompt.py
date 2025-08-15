from __future__ import annotations

from typing import List, Tuple

import tiktoken


def build_system_prompt() -> str:
    return (
        "You are a strict PDF QA assistant. Answer ONLY using the provided context.\n"
        "If the answer is not in the context, say you don't have enough information.\n"
        "Always cite sources as [page X] after the relevant sentence."
    )


def build_context(hits: list, max_tokens: int) -> tuple[str, list[dict]]:
    enc = tiktoken.get_encoding("cl100k_base")
    header = []
    used: list[dict] = []
    total_tokens = 0
    for h in hits:
        page = h.chunk.get("page_start")
        text = h.chunk.get("text", "")
        chunk_id = h.chunk.get("chunk_id")
        snippet = f"[page {page}]\n{text}\n\n"
        t = len(enc.encode(snippet))
        if total_tokens + t > max_tokens:
            break
        header.append(snippet)
        used.append({"page": page, "chunk_id": chunk_id, "text": text})
        total_tokens += t
    return ("".join(header), used)


