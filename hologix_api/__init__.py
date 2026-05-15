"""
HOLOGIX API Module

FastAPI-based REST API with OpenAI-compatible endpoints.
"""

from .main import app, create_app
from .routes import router

__all__ = ["app", "create_app", "router"]
