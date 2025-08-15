from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse


class PDFParsingError(Exception):
    """Raised when a PDF cannot be parsed."""
    pass


class DocumentNotFoundError(Exception):
    """Raised when a document is not found."""
    pass


class IngestionError(Exception):
    """Raised when document ingestion fails."""
    pass


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "code": "internal_error",
                "message": str(exc),
                "details": None,
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": "http_error",
                "message": exc.detail,
                "details": None,
            },
        )

    @app.exception_handler(PDFParsingError)
    async def pdf_parsing_error_handler(request: Request, exc: PDFParsingError):
        return JSONResponse(
            status_code=400,
            content={
                "code": "pdf_parsing_error",
                "message": str(exc),
                "details": "Consider enabling OCR if the PDF contains only images",
            },
        )

    @app.exception_handler(DocumentNotFoundError)
    async def document_not_found_handler(request: Request, exc: DocumentNotFoundError):
        return JSONResponse(
            status_code=404,
            content={
                "code": "document_not_found",
                "message": str(exc),
                "details": None,
            },
        )

    @app.exception_handler(IngestionError)
    async def ingestion_error_handler(request: Request, exc: IngestionError):
        return JSONResponse(
            status_code=500,
            content={
                "code": "ingestion_error",
                "message": str(exc),
                "details": "Document processing failed during ingestion",
            },
        )

