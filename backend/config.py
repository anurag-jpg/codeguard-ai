"""
Centralised configuration using pydantic-settings.
All secrets are loaded from environment variables / .env file.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    # ── Server ────────────────────────────────────────────────────────────────
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True
    EMBEDDING_DIMENSION: int = 768
    ALLOWED_HOSTS: List[str] = ["*"]
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # ── OpenAI / LLM ─────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = Field(default="", env="AIzaSyDUqU1ROp6kVHJaoy4SfAANVA_LXhHWCUw")
    LLM_MODEL: str = "gemini-1.5-flash"
    EMBEDDING_MODEL: str = "models/embedding-001"
    MAX_TOKENS: int = 4096
    LLM_TEMPERATURE: float = 0.1

    # ── Vector Store ─────────────────────────────────────────────────────────
    FAISS_INDEX_PATH: str = "vector_store/faiss_index"
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64
    TOP_K_RETRIEVAL: int = 8

    # ── Storage ───────────────────────────────────────────────────────────────
    DATA_DIR: str = "data"
    REPOS_DIR: str = "data/repositories"
    MAX_FILE_SIZE_MB: int = 10
    SUPPORTED_EXTENSIONS: List[str] = [
        ".py", ".js", ".ts", ".jsx", ".tsx",
        ".java", ".go", ".rs", ".cpp", ".c",
        ".cs", ".rb", ".php", ".swift", ".kt",
    ]

    # ── GitHub (optional) ─────────────────────────────────────────────────────
    GITHUB_TOKEN: str = Field(default="", env="GITHUB_TOKEN")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
