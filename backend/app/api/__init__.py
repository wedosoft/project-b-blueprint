"""API route registrations live in this package."""

from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import conversations


def register_routes(app: FastAPI) -> None:
    """Attach all API routers to the FastAPI application."""

    app.include_router(conversations.router)


__all__ = ["register_routes"]
