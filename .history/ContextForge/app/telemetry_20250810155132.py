import time
import uuid
from typing import Callable

from fastapi import FastAPI, Request


def install_telemetry(app: FastAPI) -> None:
    @app.middleware("http")
    async def add_request_context(request: Request, call_next: Callable):
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = int((time.perf_counter() - start) * 1000)
        response.headers["x-request-id"] = request_id
        response.headers["x-response-time-ms"] = str(duration_ms)
        return response

