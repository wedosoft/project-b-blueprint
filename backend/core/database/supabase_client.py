"""Supabase client initialization and utilities."""

from __future__ import annotations

from functools import lru_cache

from supabase import Client, create_client

from backend.core.config import get_settings


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Get a cached Supabase client instance.

    Returns:
        Client: Configured Supabase client with service role key for backend operations.
    """
    settings = get_settings()

    return create_client(
        supabase_url=str(settings.supabase.url),
        supabase_key=settings.supabase.service_role_key.get_secret_value(),
    )


__all__ = ["get_supabase_client"]
