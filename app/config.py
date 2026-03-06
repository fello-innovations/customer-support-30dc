from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    openai_api_key: str
    chatbot_api_key: str
    vector_store_id: str = ""
    model: str = "gpt-4o-mini"
    max_tokens: int = 1024
    session_ttl_seconds: int = 3600
    allowed_origins: str = "*"

    model_config = {"env_file": ".env", "case_sensitive": False}


@lru_cache
def get_settings() -> Settings:
    return Settings()
