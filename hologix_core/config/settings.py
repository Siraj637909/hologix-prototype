"""
HOLOGIX Settings Manager

Production-grade YAML-based configuration system with environment variable overrides.
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator
from dataclasses import dataclass, field


@dataclass
class ServerConfig:
    """Server configuration settings."""
    host: str = "127.0.0.1"
    port: int = 8080
    workers: int = 1
    reload: bool = False
    log_level: str = "info"
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    max_request_size: int = 104857600  # 100MB


@dataclass
class ModelConfig:
    """Model management configuration."""
    models_dir: str = "~/hologix/models"
    cache_dir: str = "~/hologix/cache"
    max_cache_size_gb: float = 10.0
    default_model: str = ""
    allowed_sources: List[str] = field(default_factory=lambda: ["huggingface", "local"])


@dataclass
class SecurityConfig:
    """Security configuration settings."""
    api_keys_file: str = "~/hologix/api_keys.yaml"
    key_length: int = 32
    key_prefix: str = "hx-"
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    allow_lan_access: bool = False
    trusted_ips: List[str] = field(default_factory=list)


@dataclass
class DatabaseConfig:
    """Database configuration."""
    db_path: str = "~/hologix/hologix.db"
    pool_size: int = 10
    echo: bool = False


@dataclass
class EngineConfig:
    """Inference engine configuration."""
    max_threads: int = 4
    memory_limit_mb: int = 4096
    use_mmap: bool = True
    enable_sparse: bool = False
    expert_cache_size: int = 8
    kv_cache_swap_path: str = "~/hologix/kv_swap"


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = "~/hologix/hologix.log"
    max_file_size_mb: int = 50
    backup_count: int = 5


class Settings:
    """
    Main settings manager for HOLOGIX.
    
    Loads configuration from YAML file with environment variable overrides.
    """
    
    DEFAULT_CONFIG_PATH = "~/hologix/config.yaml"
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path or os.environ.get("HOLOGIX_CONFIG", self.DEFAULT_CONFIG_PATH)).expanduser()
        self._config: Dict[str, Any] = {}
        self.server = ServerConfig()
        self.model = ModelConfig()
        self.security = SecurityConfig()
        self.database = DatabaseConfig()
        self.engine = EngineConfig()
        self.logging = LoggingConfig()
        
        if self.config_path.exists():
            self._load_from_yaml()
        
        self._apply_env_overrides()
    
    def _load_from_yaml(self) -> None:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                self._config = yaml.safe_load(f) or {}
            
            self._apply_yaml_config()
        except Exception as e:
            print(f"Warning: Could not load config from {self.config_path}: {e}")
    
    def _apply_yaml_config(self) -> None:
        """Apply YAML configuration to dataclass fields."""
        if 'server' in self._config:
            for key, value in self._config['server'].items():
                if hasattr(self.server, key):
                    setattr(self.server, key, value)
        
        if 'model' in self._config:
            for key, value in self._config['model'].items():
                if hasattr(self.model, key):
                    setattr(self.model, key, value)
        
        if 'security' in self._config:
            for key, value in self._config['security'].items():
                if hasattr(self.security, key):
                    setattr(self.security, key, value)
        
        if 'database' in self._config:
            for key, value in self._config['database'].items():
                if hasattr(self.database, key):
                    setattr(self.database, key, value)
        
        if 'engine' in self._config:
            for key, value in self._config['engine'].items():
                if hasattr(self.engine, key):
                    setattr(self.engine, key, value)
        
        if 'logging' in self._config:
            for key, value in self._config['logging'].items():
                if hasattr(self.logging, key):
                    setattr(self.logging, key, value)
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides."""
        env_mapping = {
            'HOLOGIX_HOST': ('server', 'host'),
            'HOLOGIX_PORT': ('server', 'port'),
            'HOLOGIX_WORKERS': ('server', 'workers'),
            'HOLOGIX_LOG_LEVEL': ('server', 'log_level'),
            'HOLOGIX_MODELS_DIR': ('model', 'models_dir'),
            'HOLOGIX_CACHE_DIR': ('model', 'cache_dir'),
            'HOLOGIX_DB_PATH': ('database', 'db_path'),
            'HOLOGIX_API_KEYS_FILE': ('security', 'api_keys_file'),
            'HOLOGIX_MAX_THREADS': ('engine', 'max_threads'),
            'HOLOGIX_MEMORY_LIMIT_MB': ('engine', 'memory_limit_mb'),
        }
        
        for env_var, (section, attr) in env_mapping.items():
            value = os.environ.get(env_var)
            if value is not None:
                config_obj = getattr(self, section)
                current_value = getattr(config_obj, attr)
                
                if isinstance(current_value, int):
                    value = int(value)
                elif isinstance(current_value, bool):
                    value = value.lower() in ('true', '1', 'yes')
                elif isinstance(current_value, list):
                    value = [v.strip() for v in value.split(',')]
                
                setattr(config_obj, attr, value)
    
    def save_to_yaml(self, path: Optional[str] = None) -> None:
        """Save current configuration to YAML file."""
        save_path = Path(path or self.config_path).expanduser()
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        config_dict = {
            'server': {
                'host': self.server.host,
                'port': self.server.port,
                'workers': self.server.workers,
                'reload': self.server.reload,
                'log_level': self.server.log_level,
                'cors_origins': self.server.cors_origins,
                'max_request_size': self.server.max_request_size,
            },
            'model': {
                'models_dir': self.model.models_dir,
                'cache_dir': self.model.cache_dir,
                'max_cache_size_gb': self.model.max_cache_size_gb,
                'default_model': self.model.default_model,
                'allowed_sources': self.model.allowed_sources,
            },
            'security': {
                'api_keys_file': self.security.api_keys_file,
                'key_length': self.security.key_length,
                'key_prefix': self.security.key_prefix,
                'rate_limit_requests': self.security.rate_limit_requests,
                'rate_limit_window_seconds': self.security.rate_limit_window_seconds,
                'allow_lan_access': self.security.allow_lan_access,
                'trusted_ips': self.security.trusted_ips,
            },
            'database': {
                'db_path': self.database.db_path,
                'pool_size': self.database.pool_size,
                'echo': self.database.echo,
            },
            'engine': {
                'max_threads': self.engine.max_threads,
                'memory_limit_mb': self.engine.memory_limit_mb,
                'use_mmap': self.engine.use_mmap,
                'enable_sparse': self.engine.enable_sparse,
                'expert_cache_size': self.engine.expert_cache_size,
                'kv_cache_swap_path': self.engine.kv_cache_swap_path,
            },
            'logging': {
                'level': self.logging.level,
                'format': self.logging.format,
                'file_path': self.logging.file_path,
                'max_file_size_mb': self.logging.max_file_size_mb,
                'backup_count': self.logging.backup_count,
            },
        }
        
        with open(save_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
    
    def get_models_dir(self) -> Path:
        """Get expanded models directory path."""
        return Path(self.model.models_dir).expanduser().absolute()
    
    def get_cache_dir(self) -> Path:
        """Get expanded cache directory path."""
        return Path(self.model.cache_dir).expanduser().absolute()
    
    def get_db_path(self) -> Path:
        """Get expanded database path."""
        return Path(self.database.db_path).expanduser().absolute()
    
    def get_api_keys_file(self) -> Path:
        """Get expanded API keys file path."""
        return Path(self.security.api_keys_file).expanduser().absolute()
    
    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        dirs = [
            self.get_models_dir(),
            self.get_cache_dir(),
            self.get_db_path().parent,
            self.get_api_keys_file().parent,
            Path(self.engine.kv_cache_swap_path).expanduser(),
        ]
        
        if self.logging.file_path:
            dirs.append(Path(self.logging.file_path).expanduser().parent)
        
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
