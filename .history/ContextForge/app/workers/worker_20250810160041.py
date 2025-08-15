from __future__ import annotations

import os

from redis import Redis
from rq import Connection, Worker

from app.core.config import settings


def run() -> None:  # pragma: no cover - convenience
    listen = ["ingest"]
    redis_url = os.getenv("REDIS_URL", settings.redis_url)
    conn = Redis.from_url(redis_url)
    with Connection(conn):
        worker = Worker(list(map(str, listen)))
        worker.work()


if __name__ == "__main__":  # pragma: no cover
    run()


