"""
HOLOGIX API Routes

Main router that includes all API endpoints.
"""

from fastapi import APIRouter
from .chat import router as chat_router
from .completions import router as completions_router
from .embeddings import router as embeddings_router
from .models import router as models_router
from .health import router as health_router

router = APIRouter(prefix="/v1")

# Include all route modules
router.include_router(chat_router, tags=["Chat"])
router.include_router(completions_router, tags=["Completions"])
router.include_router(embeddings_router, tags=["Embeddings"])
router.include_router(models_router, tags=["Models"])
router.include_router(health_router, tags=["Health"])

__all__ = ["router"]
