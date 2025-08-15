from __future__ import annotations

from typing import List

import fitz  # PyMuPDF

from app.core.config import settings
from app.services.parser.base import ParsedPage
from app.services.parser.ocr_base import OCRProvider


def parse_pdf_pymupdf(pdf_path: str) -> tuple[List[ParsedPage], dict]:
    doc = fitz.open(pdf_path)
    pages: list[ParsedPage] = []
    total_pages = len(doc)
    for i, page in enumerate(doc, start=1):
        text = page.get_text("text") or ""
        blocks = []
        pages.append(ParsedPage(page=i, text=text, blocks=blocks, lang=None))
    doc.close()

    if all((not p["text"]) for p in pages):
        if settings.enable_ocr:
            ocr = OCRProvider()
            return ocr.parse(pdf_path)
        raise ValueError("PDF has no extractable text; consider enabling OCR")

    return pages, {"total_pages": total_pages}


