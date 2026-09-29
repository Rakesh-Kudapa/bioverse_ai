from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven backend settings."""

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(
        default="postgresql+psycopg://bioverse:bioverse_dev@localhost:5433/bioverse"
    )
    log_level: str = "INFO"
    pubchem_timeout_seconds: float = Field(default=10.0, gt=0, le=30)
    pubchem_retry_count: int = Field(default=2, ge=0, le=4)
    pubchem_retry_backoff_seconds: float = Field(default=0.25, ge=0, le=5)
    pubchem_max_search_results: int = Field(default=10, ge=1, le=25)
    pubchem_max_structure_bytes: int = Field(default=5_000_000, ge=1_000, le=20_000_000)
    compound_cache_ttl_seconds: int = Field(default=900, ge=1, le=86_400)
    compound_cache_max_entries: int = Field(default=256, ge=1, le=10_000)
    rcsb_timeout_seconds: float = Field(default=15.0, gt=0, le=60)
    rcsb_retry_count: int = Field(default=2, ge=0, le=4)
    rcsb_retry_backoff_seconds: float = Field(default=0.5, ge=0, le=5)
    rcsb_max_search_results: int = Field(default=10, ge=1, le=25)
    rcsb_max_json_bytes: int = Field(default=5_000_000, ge=1_000, le=20_000_000)
    rcsb_max_structure_bytes: int = Field(default=25_000_000, ge=10_000, le=100_000_000)
    rcsb_cache_ttl_seconds: int = Field(default=3600, ge=1, le=86_400)
    rcsb_cache_max_entries: int = Field(default=128, ge=1, le=10_000)


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide validated settings instance."""
    return Settings()
