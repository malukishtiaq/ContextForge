from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.telemetry import install_telemetry
from app.api.routes.health import router as health_router

try:
    from app.api.routes.documents import router as documents_router
    from app.api.routes.answers import router as answers_router
except Exception:  # pragma: no cover - during early boot if deps missing
    documents_router = None
    answers_router = None


def create_app() -> FastAPI:
    app = FastAPI(title="ContextForge API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    install_telemetry(app)
    register_exception_handlers(app)

    app.include_router(health_router)
    if documents_router is not None:
        app.include_router(documents_router)
    if answers_router is not None:
        app.include_router(answers_router)

    @app.get("/")
    def root() -> dict:
        return {
            "message": "ContextForge RAG API",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/v1/health",
            "endpoints": {
                "documents": "/v1/documents",
                "answers": "/v1/answers"
            }
        }

    return app


app = create_app()

