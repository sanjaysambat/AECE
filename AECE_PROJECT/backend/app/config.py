from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Example: postgresql+psycopg://postgres:postgres@db:5432/aece
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/aece"

    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # LLM (optional). If `OPENAI_API_KEY` is not set, we fall back to a heuristic scorer.
    openai_api_key: str = ""
    llm_model: str = "gpt-4.1-mini"

    # If true, create tables on startup (useful for local dev).
    auto_create_tables: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()

