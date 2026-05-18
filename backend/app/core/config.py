from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Circle Court"
    environment: Literal["local", "staging", "production"] = "local"
    api_key: str = Field(default="dev-circle-court-key", alias="API_KEY")
    cors_origins: list[AnyHttpUrl] | list[str] = ["http://localhost:5173", "http://localhost:8000"]

    database_url: str = "sqlite+aiosqlite:///./circle_court.db"
    redis_url: str = "redis://localhost:6379/0"

    openai_api_key: str | None = None
    litellm_master_key: str | None = None
    llm_model_leader: str = "gpt-4o"
    llm_validator_models: str = "gpt-4o-mini,claude-3-5-sonnet-20241022,groq/llama-3.1-70b-versatile"
    embeddings_provider: Literal["local", "openai", "hash"] = "hash"

    circle_api_key: str | None = None
    circle_entity_secret: str | None = None
    circle_base_url: str = "https://api-sandbox.circle.com"
    circle_wallet_id: str | None = None
    circle_simulation_mode: bool = True

    web3_rpc_url: str | None = None
    escrow_contract_address: str | None = None
    deployer_private_key: str | None = None
    chain_id: int = 11155111
    web3_simulation_mode: bool = True

    upload_dir: str = "uploads"
    static_dir: str = "static"
    rate_limit: str = "120/minute"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def async_database_url(self) -> str:
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if self.database_url.startswith("postgres://"):
            return self.database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        return self.database_url

    @property
    def validator_model_list(self) -> list[str]:
        return [model.strip() for model in self.llm_validator_models.split(",") if model.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
