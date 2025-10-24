"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import get_settings

from .api import register_routes


def create_app() -> FastAPI:
    """Instantiate the FastAPI application with base metadata."""
    settings = get_settings()

    app = FastAPI(
        title="AI Contact Center API",
        version="0.1.0",
        description="Next-generation AI-powered contact center with HITL approval workflow",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            str(settings.frontend.origin),
            "http://localhost:5173",
            "http://localhost:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routes
    register_routes(app)

    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint for monitoring."""
        return {
            "status": "healthy",
            "service": "ai-contact-center-backend",
            "version": "0.1.0",
        }

    return app


app = create_app()
