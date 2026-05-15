"""
CORS Middleware Setup

Cross-Origin Resource Sharing configuration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hologix_core.config.settings import settings


def setup_cors(app: FastAPI) -> None:
    """
    Configure CORS middleware for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    cors_origins = settings.server.cors_origins
    
    # Handle wildcard
    if "*" in cors_origins:
        cors_origins = ["*"]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
            "Retry-After",
        ],
    )


class CORSMiddlewareSetup:
    """CORS middleware configuration class."""
    
    @staticmethod
    def apply(app: FastAPI) -> None:
        """Apply CORS middleware to the application."""
        setup_cors(app)
