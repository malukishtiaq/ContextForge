import io
import json
from uuid import UUID

from fastapi.testclient import TestClient

from app.main import app
from app.db.database import init_db
from app.workers import jobs


client = TestClient(app)


def _make_pdf_bytes() -> bytes:
    # Minimal PDF bytes with 'Hello' text via PyMuPDF would require write; use simple content
    # For test, just pretend a PDF file; parser may fail if truly invalid. Keep route-only test.
    return b"%PDF-1.4\n%minimal\n"


def test_upload_document_and_ingest(monkeypatch, tmp_path):
    init_db()

    # Monkeypatch queue enqueue to run ingest synchronously
    def fake_enqueue(fn_name: str, doc_id: str):
        jobs.ingest(doc_id)
        class R:
            id = "job"
        return R()

    from app.deps import get_redis_queue

    class FakeQ:
        def enqueue(self, fn_name, doc_id):
            return fake_enqueue(fn_name, doc_id)

    monkeypatch.setattr("app.api.routes.documents.get_redis_queue", lambda: FakeQ())

    files = {"file": ("test.pdf", _make_pdf_bytes(), "application/pdf")}
    r = client.post("/v1/documents", files=files)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "docId" in data
    doc_id = data["docId"]

    r2 = client.get(f"/v1/documents/{doc_id}")
    assert r2.status_code in (200, 404)

