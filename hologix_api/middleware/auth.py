"""
Authentication Middleware

API key authentication and user management.
"""

import time
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from hologix_core.config.settings import settings
from hologix_core.utils.helpers import hash_string


security = HTTPBearer(auto_error=False)


class APIKeyManager:
    """Manages API keys for authentication."""
    
    _keys: Optional[Dict[str, Dict[str, Any]]] = None
    _last_load: float = 0
    _cache_ttl: float = 60.0  # Cache TTL in seconds
    
    @classmethod
    def _load_keys(cls) -> Dict[str, Dict[str, Any]]:
        """Load API keys from file."""
        import yaml
        from pathlib import Path
        
        keys_file = Path(settings.security.api_keys_file).expanduser()
        
        if not keys_file.exists():
            return {}
        
        try:
            with open(keys_file, 'r') as f:
                data = yaml.safe_load(f) or {}
            
            # Normalize keys structure
            keys = {}
            for key_id, key_data in data.get('keys', {}).items():
                if isinstance(key_data, dict):
                    keys[key_id] = key_data
                else:
                    # Simple format: just the key name
                    keys[key_id] = {
                        'name': key_data,
                        'created': int(time.time()),
                        'active': True,
                    }
            
            return keys
        except Exception:
            return {}
    
    @classmethod
    def get_keys(cls) -> Dict[str, Dict[str, Any]]:
        """Get cached API keys."""
        now = time.time()
        
        if cls._keys is None or (now - cls._last_load) > cls._cache_ttl:
            cls._keys = cls._load_keys()
            cls._last_load = now
        
        return cls._keys
    
    @classmethod
    def reload_keys(cls) -> None:
        """Force reload of API keys."""
        cls._keys = cls._load_keys()
        cls._last_load = time.time()
    
    @classmethod
    def validate_key(cls, key: str) -> Optional[Dict[str, Any]]:
        """Validate an API key and return key info if valid."""
        keys = cls.get_keys()
        
        # Check direct match
        if key in keys:
            key_info = keys[key]
            if key_info.get('active', True):
                return key_info
        
        # Check hashed keys (for secure storage)
        key_hash = hash_string(key)
        for stored_key, key_info in keys.items():
            if stored_key.startswith('hash:'):
                stored_hash = stored_key[5:]
                if stored_hash == key_hash and key_info.get('active', True):
                    return key_info
        
        return None


async def verify_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    request: Optional[Request] = None,
) -> Dict[str, Any]:
    """
    Verify API key from request.
    
    Checks Authorization header (Bearer token) or X-API-Key header.
    """
    # Allow bypass if auth is disabled (development)
    if not settings.security.api_keys_file:
        return {"user": "anonymous", "key": None}
    
    api_key = None
    
    # Try Bearer token
    if credentials and credentials.credentials:
        api_key = credentials.credentials
    
    # Try X-API-Key header
    if request and not api_key:
        api_key = request.headers.get('X-API-Key')
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Validate key
    key_info = APIKeyManager.validate_key(api_key)
    
    if not key_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if key is active
    if not key_info.get('active', True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is deactivated",
        )
    
    return {
        "user": key_info.get('name', 'unknown'),
        "key": api_key[:8] + "..." if len(api_key) > 8 else api_key,
        "key_info": key_info,
    }


async def get_current_user(
    user: Dict[str, Any] = Depends(verify_api_key),
) -> Dict[str, Any]:
    """Get current authenticated user."""
    return user


class AuthMiddleware:
    """Authentication middleware for FastAPI app."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        # Authentication is handled via dependencies
        await self.app(scope, receive, send)
