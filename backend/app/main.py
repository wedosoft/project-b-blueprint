"""FastAPI application entry point."""

from fastapi import FastAPI

from backend.app.api import register_routes


def create_app() -> FastAPI:
    """Instantiate the FastAPI application with base metadata."""
    app = FastAPI(title="AI Contact Center API", version="0.1.0")
    register_routes(app)
    return app


app = create_app()
