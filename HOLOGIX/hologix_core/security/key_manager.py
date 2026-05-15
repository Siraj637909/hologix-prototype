"""
HOLOGIX Security - API Key Manager
Production-grade API key generation, hashing, and validation.
"""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from hologix_core.constants.env_manager import env
from hologix_core.database.models import APIKey
from hologix_core.database import get_session
from hologix_core.logger import get_logger
from hologix_core.exceptions import (
    InvalidAPIKeyError,
    ExpiredAPIKeyError,
    RateLimitExceededError,
)

logger = get_logger("security")


class APIKeyManager:
    """Manages API key lifecycle including creation, validation, and rate limiting."""
    
    _instance: Optional["APIKeyManager"] = None
    
    def __new__(cls) -> "APIKeyManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        if self._initialized:
            return
        
        self.key_prefix = env.API_KEY_PREFIX
        self.expiry_days = env.config.get("api_key_expiry_days", 365)
        self.rate_limit_rpm = env.config.get("rate_limit_requests_per_minute", 60)
        self.rate_limit_tpm = env.config.get("rate_limit_tokens_per_minute", 10000)
        
        self._initialized = True
        logger.info("API Key Manager initialized")
    
    def _hash_key(self, key: str) -> str:
        """Hash API key using SHA256 for secure storage."""
        return hashlib.sha256(key.encode()).hexdigest()
    
    def generate_api_key(self, name: Optional[str] = None) -> Tuple[str, dict]:
        """
        Generate a new API key.
        
        Returns:
            Tuple of (raw_key, key_info) where raw_key should only be shown once to user.
        """
        # Generate cryptographically secure random key
        random_part = secrets.token_hex(24)  # 48 hex chars
        raw_key = f"{self.key_prefix}{random_part}"
        
        # Compute hash for storage
        key_hash = self._hash_key(raw_key)
        key_prefix_display = raw_key[:12]  # Show first 12 chars for identification
        
        # Calculate expiry
        expires_at = datetime.utcnow() + timedelta(days=self.expiry_days)
        
        # Store in database
        with get_session() as session:
            api_key = APIKey(
                key_hash=key_hash,
                key_prefix=key_prefix_display,
                name=name,
                expires_at=expires_at,
                is_active=True,
            )
            session.add(api_key)
            session.commit()
            session.refresh(api_key)
        
        logger.info(f"Generated new API key ID {api_key.id} with prefix {key_prefix_display}")
        
        key_info = {
            "id": api_key.id,
            "key_prefix": key_prefix_display,
            "name": name,
            "created_at": api_key.created_at.isoformat(),
            "expires_at": expires_at.isoformat(),
        }
        
        return raw_key, key_info
    
    def validate_api_key(self, api_key: str) -> APIKey:
        """
        Validate an API key and return the database record.
        
        Raises:
            InvalidAPIKeyError: If key is invalid or inactive
            ExpiredAPIKeyError: If key has expired
        """
        key_hash = self._hash_key(api_key)
        
        with get_session() as session:
            stmt = select(APIKey).where(APIKey.key_hash == key_hash)
            key_record = session.execute(stmt).scalar_one_or_none()
            
            if not key_record:
                logger.warning(f"Invalid API key attempt with hash prefix: {key_hash[:8]}")
                raise InvalidAPIKeyError()
            
            # Check if active
            if not key_record.is_active:
                logger.warning(f"Inactive API key used: {key_record.key_prefix}")
                raise InvalidAPIKeyError()
            
            # Check expiry
            if key_record.expires_at and key_record.expires_at < datetime.utcnow():
                logger.warning(f"Expired API key used: {key_record.key_prefix}")
                raise ExpiredAPIKeyError(str(key_record.id))
            
            # Update last used timestamp
            key_record.last_used_at = datetime.utcnow()
            session.commit()
            
            return key_record
    
    def check_rate_limit(self, api_key_id: int, tokens: int = 1) -> bool:
        """
        Check and update rate limit for an API key.
        
        Args:
            api_key_id: Database ID of the API key
            tokens: Number of tokens for this request
            
        Returns:
            True if within rate limits
            
        Raises:
            RateLimitExceededError: If rate limit exceeded
        """
        now = datetime.utcnow()
        
        with get_session() as session:
            stmt = select(APIKey).where(APIKey.id == api_key_id)
            key_record = session.execute(stmt).scalar_one_or_none()
            
            if not key_record:
                return True
            
            # Reset counter if minute has passed
            if key_record.minute_reset_at is None or now > key_record.minute_reset_at:
                key_record.requests_this_minute = 0
                key_record.minute_reset_at = now + timedelta(minutes=1)
            
            # Check request rate limit
            if key_record.requests_this_minute >= self.rate_limit_rpm:
                retry_after = int((key_record.minute_reset_at - now).total_seconds())
                raise RateLimitExceededError(self.rate_limit_rpm, retry_after)
            
            # Increment counters
            key_record.requests_this_minute += 1
            key_record.total_requests += 1
            key_record.total_tokens += tokens
            
            session.commit()
            
            return True
    
    def revoke_key(self, api_key_id: int) -> bool:
        """Revoke an API key by ID."""
        with get_session() as session:
            stmt = (
                update(APIKey)
                .where(APIKey.id == api_key_id)
                .values(is_active=False)
            )
            result = session.execute(stmt)
            session.commit()
            
            revoked = result.rowcount > 0
            if revoked:
                logger.info(f"Revoked API key ID {api_key_id}")
            
            return revoked
    
    def list_keys(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """List all API keys (without exposing the actual keys)."""
        with get_session() as session:
            stmt = (
                select(APIKey)
                .order_by(APIKey.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            keys = session.execute(stmt).scalars().all()
            
            return [
                {
                    "id": k.id,
                    "key_prefix": k.key_prefix,
                    "name": k.name,
                    "is_active": k.is_active,
                    "created_at": k.created_at.isoformat(),
                    "expires_at": k.expires_at.isoformat() if k.expires_at else None,
                    "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
                    "total_requests": k.total_requests,
                    "total_tokens": k.total_tokens,
                }
                for k in keys
            ]
    
    def get_key_stats(self, api_key_id: int) -> Optional[dict]:
        """Get usage statistics for a specific API key."""
        with get_session() as session:
            stmt = select(APIKey).where(APIKey.id == api_key_id)
            key_record = session.execute(stmt).scalar_one_or_none()
            
            if not key_record:
                return None
            
            return {
                "id": key_record.id,
                "key_prefix": key_record.key_prefix,
                "name": key_record.name,
                "is_active": key_record.is_active,
                "total_requests": key_record.total_requests,
                "total_tokens": key_record.total_tokens,
                "requests_this_minute": key_record.requests_this_minute,
                "created_at": key_record.created_at.isoformat(),
                "last_used_at": key_record.last_used_at.isoformat() if key_record.last_used_at else None,
            }
    
    def cleanup_expired_keys(self) -> int:
        """Deactivate all expired keys."""
        with get_session() as session:
            stmt = (
                update(APIKey)
                .where(
                    (APIKey.expires_at < datetime.utcnow()) &
                    (APIKey.is_active == True)
                )
                .values(is_active=False)
            )
            result = session.execute(stmt)
            session.commit()
            
            cleaned = result.rowcount
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} expired API keys")
            
            return cleaned


# =============================================================================
# Global Instance
# =============================================================================

def get_api_key_manager() -> APIKeyManager:
    """Get the global API key manager instance."""
    return APIKeyManager()


api_key_manager = APIKeyManager()

