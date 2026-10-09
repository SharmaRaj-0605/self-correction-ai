from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gemini_api_key: str
    gemini_model: str = "gemini-3.8-flash"
    gemini_fallback_model: str = ""
    gemini_max_retries: int = 5
    redis_url: str = "redis://127.0.0.1:6379/0"
    cache_ttl_seconds: int = 900
    max_iterations: int = 3
    min_accept_score: float = 8.0
    use_web_search: bool = False
    max_input_chars: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
