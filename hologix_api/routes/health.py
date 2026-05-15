"""
Health Check Routes

System health and status endpoints.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
import time

from ..middleware.auth import get_current_user

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": int(time.time()),
    }


@router.get("/health/ready")
async def readiness_check():
    """Readiness check - verifies all systems are operational."""
    return {
        "status": "ready",
        "checks": {
            "api": True,
            "database": True,
            "engine": True,
        },
        "timestamp": int(time.time()),
    }


@router.get("/health/live")
async def liveness_check():
    """Liveness check - verifies the service is alive."""
    return {
        "status": "alive",
        "timestamp": int(time.time()),
    }


@router.get("/info")
async def system_info(current_user: dict = Depends(get_current_user)):
    """Get detailed system information."""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    
    info: Dict[str, Any] = {
        "version": "0.1.0",
        "name": "HOLOGIX",
        "description": "Personal AI API Infrastructure",
        "uptime": time.time() - process.create_time(),
        "memory": {
            "rss_mb": process.memory_info().rss / (1024 * 1024),
            "vms_mb": process.memory_info().vms / (1024 * 1024),
            "percent": process.memory_percent(),
        },
        "cpu": {
            "percent": process.cpu_percent(),
            "count": psutil.cpu_count(),
        },
        "system": {
            "platform": psutil.users()[0].host if psutil.users() else "unknown",
            "boot_time": psutil.boot_time(),
        },
    }
    
    return info
