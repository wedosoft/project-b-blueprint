"""Centralized configuration loading for the backend application."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, SecretStr

_ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(_ROOT_DIR / ".env", override=False)


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _get_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(f"Environment variable {name!r} must be an integer.") from exc


def _get_bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class SupabaseSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")

    url: HttpUrl
    service_role_key: SecretStr
    anon_key: SecretStr
    jwt_secret: SecretStr | None = None


class QdrantSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")

    url: HttpUrl
    api_key: SecretStr
    collection: str = Field(default="ccos-mvp", min_length=1)
    vector_dimension: int = Field(default=1536, ge=1)


class LLMSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")

    provider: Literal["openai", "anthropic"] = "openai"
    openai_api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None
    default_model: str = "gpt-4.1-mini"
    fallback_model: str | None = None
    request_timeout_seconds: int = Field(default=30, ge=1)

    def require_api_key(self) -> SecretStr:
        if self.provider == "openai" and self.openai_api_key:
            return self.openai_api_key
        if self.provider == "anthropic" and self.anthropic_api_key:
            return self.anthropic_api_key
        raise RuntimeError(f"No API key configured for LLM provider '{self.provider}'.")


class FlySettings(BaseModel):
    model_config = ConfigDict(extra="ignore")

    app_name: str
    api_token: SecretStr | None = None


class BackendSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")

    base_url: HttpUrl = Field(default="http://localhost:8000")
    log_level: str = Field(default="INFO")
    scheduler_enabled: bool = Field(default=True)


class FrontendSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")

    origin: HttpUrl = Field(default="http://localhost:5173")


class Settings(BaseModel):
    model_config = ConfigDict(extra="ignore")

    environment: Literal["development", "staging", "production"] = "development"
    supabase: SupabaseSettings
    qdrant: QdrantSettings
    llm: LLMSettings
    fly: FlySettings
    backend: BackendSettings
    frontend: FrontendSettings

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load configuration from the environment once and cache the result."""
    return Settings(
        environment=os.getenv("APP_ENV", "development"),
        supabase=SupabaseSettings(
            url=_require_env("SUPABASE_URL"),
            service_role_key=SecretStr(_require_env("SUPABASE_SERVICE_ROLE_KEY")),
            anon_key=SecretStr(_require_env("SUPABASE_ANON_KEY")),
            jwt_secret=(
                SecretStr(jwt) if (jwt := os.getenv("SUPABASE_JWT_SECRET")) else None
            ),
        ),
        qdrant=QdrantSettings(
            url=_require_env("QDRANT_URL"),
            api_key=SecretStr(_require_env("QDRANT_API_KEY")),
            collection=os.getenv("QDRANT_COLLECTION", "ccos-mvp"),
            vector_dimension=_get_int_env("QDRANT_VECTOR_DIMENSION", 1536),
        ),
        llm=LLMSettings(
            provider=os.getenv("LLM_PROVIDER", "openai"),  # type: ignore[arg-type]
            openai_api_key=(
                SecretStr(api_key) if (api_key := os.getenv("OPENAI_API_KEY")) else None
            ),
            anthropic_api_key=(
                SecretStr(api_key) if (api_key := os.getenv("ANTHROPIC_API_KEY")) else None
            ),
            default_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            fallback_model=os.getenv("LLM_FALLBACK_MODEL"),
            request_timeout_seconds=int(os.getenv("LLM_TIMEOUT_SECONDS", "30")),
        ),
        fly=FlySettings(
            app_name=_require_env("FLY_APP_NAME"),
            api_token=(
                SecretStr(token) if (token := os.getenv("FLY_API_TOKEN")) else None
            ),
        ),
        backend=BackendSettings(
            base_url=_require_env("BACKEND_BASE_URL"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            scheduler_enabled=_get_bool_env("SCHEDULER_ENABLED", True),
        ),
        frontend=FrontendSettings(
            origin=_require_env("FRONTEND_ORIGIN"),
        ),
    )


__all__ = [
    "BackendSettings",
    "FlySettings",
    "FrontendSettings",
    "LLMSettings",
    "QdrantSettings",
    "Settings",
    "SupabaseSettings",
    "get_settings",
]
