"""FastAPI application entry point."""

from fastapi import FastAPI


def create_app() -> FastAPI:
    """Instantiate the FastAPI application with base metadata."""
    app = FastAPI(title="AI Contact Center API", version="0.1.0")
    return app


app = create_app()
