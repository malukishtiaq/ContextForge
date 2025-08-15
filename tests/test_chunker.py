from app.services.chunker.chunker import chunk_pages


def test_chunker_basic():
    pages = [
        {"page": 1, "text": "Hello world. This is a test document. " * 50, "blocks": [], "lang": None}
    ]
    chunks, stats = chunk_pages("doc123", pages)
    assert len(chunks) >= 1
    assert stats["chunks"] == len(chunks)
    assert all(c.page_start == 1 for c in chunks)

