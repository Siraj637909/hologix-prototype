"""
Rate Limiting Middleware

Request rate limiting to prevent abuse.
"""

import time
from typing import Dict, List, Optional
from collections import defaultdict
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from hologix_core.config.settings import settings


class RateLimiter:
    """Sliding window rate limiter."""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = defaultdict(list)
    
    def is_allowed(self, key: str) -> tuple[bool, int, float]:
        """
        Check if request is allowed.
        
        Returns:
            Tuple of (allowed, remaining, reset_time)
        """
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        self.requests[key] = [t for t in self.requests[key] if t > window_start]
        
        current_count = len(self.requests[key])
        remaining = max(0, self.max_requests - current_count)
        reset_time = now + self.window_seconds
        
        if self.requests[key]:
            reset_time = self.requests[key][0] + self.window_seconds
        
        if current_count >= self.max_requests:
            return False, 0, reset_time
        
        self.requests[key].append(now)
        return True, remaining - 1, reset_time
    
    def get_headers(self, key: str) -> Dict[str, str]:
        """Get rate limit headers for response."""
        _, remaining, reset_time = self.is_allowed(key)
        now = time.time()
        
        return {
            'X-RateLimit-Limit': str(self.max_requests),
            'X-RateLimit-Remaining': str(max(0, remaining)),
            'X-RateLimit-Reset': str(int(reset_time)),
            'Retry-After': str(max(0, int(reset_time - now))),
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware for FastAPI."""
    
    def __init__(
        self,
        app,
        max_requests: Optional[int] = None,
        window_seconds: Optional[int] = None,
        exclude_paths: Optional[List[str]] = None,
    ):
        super().__init__(app)
        self.limiter = RateLimiter(
            max_requests=max_requests or settings.security.rate_limit_requests,
            window_seconds=window_seconds or settings.security.rate_limit_window_seconds,
        )
        self.exclude_paths = exclude_paths or ['/health', '/health/live', '/docs', '/openapi.json']
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for excluded paths
        path = request.url.path
        if any(path.startswith(exclude) for exclude in self.exclude_paths):
            return await call_next(request)
        
        # Get client identifier
        client_ip = self._get_client_ip(request)
        api_key = request.headers.get('X-API-Key', '')
        
        # Use API key if available, otherwise use IP
        key = f"{api_key}:{client_ip}" if api_key else f"ip:{client_ip}"
        
        # Check rate limit
        allowed, remaining, reset_time = self.limiter.is_allowed(key)
        
        if not allowed:
            retry_after = int(reset_time - time.time())
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "code": 1003,
                        "message": "Rate limit exceeded",
                        "retry_after": max(0, retry_after),
                    }
                },
                headers=self.limiter.get_headers(key),
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        for header, value in self.limiter.get_headers(key).items():
            response.headers[header] = value
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check X-Forwarded-For header
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        if request.client:
            return request.client.host
        
        return "unknown"
