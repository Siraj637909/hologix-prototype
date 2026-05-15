"""
HOLOGIX Core Utilities

Common utility functions used throughout the HOLOGIX system.
"""

import hashlib
import secrets
import time
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar
from datetime import datetime, timedelta
import threading
import functools

T = TypeVar('T')


def generate_api_key(length: int = 32, prefix: str = "hx-") -> str:
    """
    Generate a secure random API key.
    
    Args:
        length: Length of the random part
        prefix: Prefix for the key
        
    Returns:
        Generated API key
    """
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    random_part = ''.join(secrets.choice(alphabet) for _ in range(length))
    return f"{prefix}{random_part}"


def hash_string(value: str, algorithm: str = "sha256") -> str:
    """
    Hash a string using the specified algorithm.
    
    Args:
        value: String to hash
        algorithm: Hash algorithm (md5, sha1, sha256, sha512)
        
    Returns:
        Hex-encoded hash
    """
    hash_func = getattr(hashlib, algorithm, hashlib.sha256)
    return hash_func(value.encode()).hexdigest()


def format_bytes(size: int) -> str:
    """
    Format bytes into human-readable size.
    
    Args:
        size: Size in bytes
        
    Returns:
        Human-readable size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(size) < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Human-readable duration string
    """
    if seconds < 0.001:
        return f"{seconds * 1000000:.0f}µs"
    elif seconds < 1:
        return f"{seconds * 1000:.2f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def parse_size(size_str: str) -> int:
    """
    Parse human-readable size string to bytes.
    
    Args:
        size_str: Size string (e.g., "1.5GB", "512MB")
        
    Returns:
        Size in bytes
    """
    units = {
        'B': 1,
        'KB': 1024,
        'MB': 1024 ** 2,
        'GB': 1024 ** 3,
        'TB': 1024 ** 4,
    }
    
    size_str = size_str.strip().upper()
    
    for unit, multiplier in sorted(units.items(), key=lambda x: -len(x[0])):
        if size_str.endswith(unit):
            number = float(size_str[:-len(unit)].strip())
            return int(number * multiplier)
    
    return int(float(size_str))


def get_timestamp() -> int:
    """Get current Unix timestamp."""
    return int(time.time())


def get_iso_timestamp() -> str:
    """Get current ISO 8601 timestamp."""
    return datetime.utcnow().isoformat() + "Z"


def parse_iso_timestamp(timestamp: str) -> datetime:
    """Parse ISO 8601 timestamp to datetime."""
    if timestamp.endswith('Z'):
        timestamp = timestamp[:-1] + '+00:00'
    return datetime.fromisoformat(timestamp)


async def retry_async(
    func: Callable,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Any:
    """
    Retry an async function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_retries: Maximum number of retries
        delay: Initial delay between retries
        backoff: Backoff multiplier
        exceptions: Exceptions to catch
        
    Returns:
        Result of the function
        
    Raises:
        Last exception if all retries fail
    """
    current_delay = delay
    
    for attempt in range(max_retries):
        try:
            return await func()
        except exceptions as e:
            if attempt == max_retries - 1:
                raise
            
            await asyncio.sleep(current_delay)
            current_delay *= backoff
    
    return None  # Should never reach here


def retry_sync(
    func: Callable,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Any:
    """
    Retry a sync function with exponential backoff.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        delay: Initial delay between retries
        backoff: Backoff multiplier
        exceptions: Exceptions to catch
        
    Returns:
        Result of the function
        
    Raises:
        Last exception if all retries fail
    """
    current_delay = delay
    
    for attempt in range(max_retries):
        try:
            return func()
        except exceptions as e:
            if attempt == max_retries - 1:
                raise
            
            time.sleep(current_delay)
            current_delay *= backoff
    
    return None  # Should never reach here


class RateLimiter:
    """Simple rate limiter implementation."""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = {}
        self._lock = threading.Lock()
    
    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed for the given key."""
        now = time.time()
        window_start = now - self.window_seconds
        
        with self._lock:
            if key not in self.requests:
                self.requests[key] = []
            
            # Remove old requests
            self.requests[key] = [t for t in self.requests[key] if t > window_start]
            
            if len(self.requests[key]) >= self.max_requests:
                return False
            
            self.requests[key].append(now)
            return True
    
    def get_remaining(self, key: str) -> int:
        """Get remaining requests for the given key."""
        now = time.time()
        window_start = now - self.window_seconds
        
        with self._lock:
            if key not in self.requests:
                return self.max_requests
            
            current_count = len([t for t in self.requests[key] if t > window_start])
            return max(0, self.max_requests - current_count)
    
    def get_reset_time(self, key: str) -> float:
        """Get time until rate limit resets."""
        now = time.time()
        window_start = now - self.window_seconds
        
        with self._lock:
            if key not in self.requests or not self.requests[key]:
                return now
            
            oldest_request = min(t for t in self.requests[key] if t > window_start)
            return oldest_request + self.window_seconds


class LRUCache:
    """Simple LRU cache implementation."""
    
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache: Dict[Any, Any] = {}
        self.order: List[Any] = []
        self._lock = threading.Lock()
    
    def get(self, key: Any, default: Any = None) -> Any:
        """Get item from cache."""
        with self._lock:
            if key in self.cache:
                # Move to end (most recently used)
                self.order.remove(key)
                self.order.append(key)
                return self.cache[key]
            return default
    
    def put(self, key: Any, value: Any) -> None:
        """Put item in cache."""
        with self._lock:
            if key in self.cache:
                self.order.remove(key)
            elif len(self.cache) >= self.capacity:
                # Remove least recently used
                oldest = self.order.pop(0)
                del self.cache[oldest]
            
            self.cache[key] = value
            self.order.append(key)
    
    def delete(self, key: Any) -> bool:
        """Delete item from cache."""
        with self._lock:
            if key in self.cache:
                self.order.remove(key)
                del self.cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear the cache."""
        with self._lock:
            self.cache.clear()
            self.order.clear()
    
    def __contains__(self, key: Any) -> bool:
        return key in self.cache
    
    def __len__(self) -> int:
        return len(self.cache)


def memoize(func: Callable[..., T]) -> Callable[..., T]:
    """Simple memoization decorator."""
    cache: Dict[str, T] = {}
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> T:
        key = str(args) + str(sorted(kwargs.items()))
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]
    
    return wrapper


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to maximum length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing invalid characters."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()


def chunk_list(lst: List[T], chunk_size: int) -> List[List[T]]:
    """Split a list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


async def gather_with_concurrency(n: int, *coros) -> List[Any]:
    """Run coroutines with limited concurrency."""
    semaphore = asyncio.Semaphore(n)
    
    async def limited_coro(coro):
        async with semaphore:
            return await coro
    
    return await asyncio.gather(*(limited_coro(c) for c in coros))


def ensure_path(path: Union[str, Path], is_file: bool = False) -> Path:
    """Ensure path exists, creating directories as needed."""
    path_obj = Path(path).expanduser()
    
    if is_file:
        path_obj.parent.mkdir(parents=True, exist_ok=True)
    else:
        path_obj.mkdir(parents=True, exist_ok=True)
    
    return path_obj


def deep_merge(base: Dict, override: Dict) -> Dict:
    """Deep merge two dictionaries."""
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result
