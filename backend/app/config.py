"""Application settings. Everything environment-driven so the same code runs
on SQLite (dev/test) and Postgres (compose/prod), with Gemini or Mock AI."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Financial Statement"
    version: str = "0.1.0"
    database_url: str = "sqlite:///./financial-statement.db"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 720
    ai_provider: str = "mock"  # mock | gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    anomaly_pct_threshold: float = 50.0
    ai_max_critique_loops: int = 2  # bound on the self-criticism revise loop
    filing_deadline_months: int = 4
    cors_origins: str = "*"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
