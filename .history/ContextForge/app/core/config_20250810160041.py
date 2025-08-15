from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8080
    cors_origins: str = "*"

    data_dir: str = "./data"

    sqlite_path: str = "./data/meta.db"

    redis_url: str = "redis://localhost:6379/0"

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    embedding_model: str = "text-embedding-3-small"
    chat_model: str = "gpt-4o-mini"

    enable_ocr: bool = False
    enable_rerank: bool = False
    max_context_tokens: int = 2000
    top_k: int = 10
    top_k_final: int = 6
    sim_threshold_max: float = 0.30
    sim_threshold_avg: float = 0.26
    chunk_target_tokens: int = 800
    chunk_overlap_tokens: int = 100

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

