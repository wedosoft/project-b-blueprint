"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .api import register_routes


def create_app() -> FastAPI:
    """Instantiate the FastAPI application with base metadata."""
    app = FastAPI(title="AI Contact Center API", version="0.1.0")

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return JSONResponse({
            "status": "ok",
            "service": "AI Contact Center API",
            "version": "0.1.0"
        })

    # Root redirect to docs
    @app.get("/")
    async def root():
        """Root endpoint redirects to API documentation."""
        return JSONResponse({
            "message": "AI Contact Center API",
            "docs": "/docs",
            "health": "/health"
        })

    register_routes(app)
    return app


app = create_app()
