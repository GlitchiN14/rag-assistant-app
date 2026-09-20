"""Application settings, loaded from environment variables / a .env file."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ directory (two levels above app/core/config.py -> app -> backend)
BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "Cybersecurity Guidelines Assistant"
    log_level: str = "INFO"

    # Ollama
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    temperature: float = 0.1

    # Retrieval
    vector_store_dir: str = "data/vector_store"
    top_k: int = 4
    max_distance: float = 0.65

    # CORS (comma-separated)
    cors_origins: str = "http://localhost:8501,http://127.0.0.1:8501"

    @property
    def vector_store_path(self) -> Path:
        path = Path(self.vector_store_dir)
        return path if path.is_absolute() else BACKEND_DIR / path

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
