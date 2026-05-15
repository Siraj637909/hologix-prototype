"""
HOLOGIX Constants and Environment Manager
Production-grade configuration management for local AI infrastructure.
"""
import os
from pathlib import Path
from typing import Optional
import yaml


class EnvManager:
    """Centralized environment variable and path management."""
    
    # Core paths
    HOLOGIX_ROOT = Path(__file__).parent.parent.parent
    CONFIG_DIR = HOLOGIX_ROOT / "hologix_core" / "config"
    DATA_DIR = HOLOGIX_ROOT / "data"
    MODELS_DIR = DATA_DIR / "models"
    CACHE_DIR = DATA_DIR / "cache"
    LOGS_DIR = DATA_DIR / "logs"
    ARTIFACTS_DIR = DATA_DIR / "artifacts"
    DB_PATH = DATA_DIR / "hologix.db"
    
    # API defaults
    DEFAULT_HOST = "127.0.0.1"
    DEFAULT_PORT = 11435
    
    # Security
    API_KEY_PREFIX = "hgx_sk_"
    API_KEY_LENGTH = 32
    
    # Model defaults
    DEFAULT_MODEL_CONTEXT_LENGTH = 4096
    DEFAULT_MAX_TOKENS = 2048
    
    # Engine defaults
    ENGINE_THREADS = 4
    ENGINE_BATCH_SIZE = 512
    
    def __init__(self):
        self._ensure_directories()
        self._config: Optional[dict] = None
    
    def _ensure_directories(self) -> None:
        """Create all required directories if they don't exist."""
        for directory in [
            self.DATA_DIR,
            self.MODELS_DIR,
            self.CACHE_DIR,
            self.LOGS_DIR,
            self.ARTIFACTS_DIR,
        ]:
            directory.mkdir(parents=True, exist_ok=True)
    
    @property
    def config(self) -> dict:
        """Lazy-load configuration from YAML."""
        if self._config is None:
            self._config = self._load_config()
        return self._config
    
    def _load_config(self) -> dict:
        """Load configuration from settings.yaml."""
        config_path = self.CONFIG_DIR / "settings.yaml"
        if config_path.exists():
            with open(config_path, "r") as f:
                return yaml.safe_load(f) or {}
        return {}
    
    def get(self, key: str, default=None):
        """Get a configuration value."""
        return self.config.get(key, default)
    
    def reload_config(self) -> dict:
        """Force reload configuration from disk."""
        self._config = self._load_config()
        return self._config
    
    @property
    def api_port(self) -> int:
        """Get API port from config or default."""
        return int(os.getenv("HOLOGIX_PORT", self.config.get("api_port", self.DEFAULT_PORT)))
    
    @property
    def api_host(self) -> str:
        """Get API host from config or default."""
        return os.getenv("HOLOGIX_HOST", self.config.get("api_host", self.DEFAULT_HOST))
    
    @property
    def debug_mode(self) -> bool:
        """Check if debug mode is enabled."""
        return bool(os.getenv("HOLOGIX_DEBUG", self.config.get("debug_mode", False)))
    
    @property
    def max_request_size(self) -> int:
        """Maximum request size in bytes."""
        return int(os.getenv("HOLOGIX_MAX_REQUEST_SIZE", 
                            self.config.get("max_request_size", 10 * 1024 * 1024)))


# Global singleton instance
env = EnvManager()


def get_env() -> EnvManager:
    """Get the global environment manager instance."""
    return env
