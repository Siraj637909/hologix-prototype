"""
HOLOGIX Environment Manager

Handles environment variable management and validation.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class EnvVar:
    """Environment variable definition."""
    name: str
    default: Any = None
    required: bool = False
    var_type: type = str
    description: str = ""


class EnvManager:
    """
    Environment variable manager for HOLOGIX.
    
    Provides centralized environment variable handling with validation,
    type conversion, and default values.
    """
    
    DEFINED_VARS: List[EnvVar] = [
        EnvVar("HOLOGIX_HOST", default="127.0.0.1", description="Server host"),
        EnvVar("HOLOGIX_PORT", default=8080, var_type=int, description="Server port"),
        EnvVar("HOLOGIX_WORKERS", default=1, var_type=int, description="Number of worker processes"),
        EnvVar("HOLOGIX_LOG_LEVEL", default="INFO", description="Logging level"),
        EnvVar("HOLOGIX_CONFIG", default="~/hologix/config.yaml", description="Config file path"),
        EnvVar("HOLOGIX_MODELS_DIR", default="~/hologix/models", description="Models directory"),
        EnvVar("HOLOGIX_CACHE_DIR", default="~/hologix/cache", description="Cache directory"),
        EnvVar("HOLOGIX_DB_PATH", default="~/hologix/hologix.db", description="Database path"),
        EnvVar("HOLOGIX_API_KEYS_FILE", default="~/hologix/api_keys.yaml", description="API keys file"),
        EnvVar("HOLOGIX_MAX_THREADS", default=4, var_type=int, description="Max inference threads"),
        EnvVar("HOLOGIX_MEMORY_LIMIT_MB", default=4096, var_type=int, description="Memory limit in MB"),
        EnvVar("HOLOGIX_DEBUG", default=False, var_type=bool, description="Enable debug mode"),
        EnvVar("HOLOGIX_ALLOW_LAN", default=False, var_type=bool, description="Allow LAN access"),
        EnvVar("HOLOGIX_RATE_LIMIT", default=100, var_type=int, description="Rate limit requests"),
        EnvVar("HOLOGIX_SECRET_KEY", default=None, required=False, description="Secret key for signing"),
    ]
    
    def __init__(self):
        self._vars: Dict[str, Any] = {}
        self._load_all()
    
    def _convert_value(self, value: str, var_type: type) -> Any:
        """Convert string value to specified type."""
        if var_type == bool:
            return value.lower() in ('true', '1', 'yes', 'on')
        elif var_type == int:
            return int(value)
        elif var_type == float:
            return float(value)
        elif var_type == list:
            return [v.strip() for v in value.split(',')] if value else []
        else:
            return value
    
    def _load_all(self) -> None:
        """Load all defined environment variables."""
        for env_var in self.DEFINED_VARS:
            value = os.environ.get(env_var.name)
            
            if value is not None:
                try:
                    self._vars[env_var.name] = self._convert_value(value, env_var.var_type)
                except (ValueError, TypeError) as e:
                    print(f"Warning: Invalid value for {env_var.name}: {value} ({e})")
                    self._vars[env_var.name] = env_var.default
            else:
                self._vars[env_var.name] = env_var.default
    
    def get(self, name: str, default: Any = None) -> Any:
        """Get environment variable value."""
        return self._vars.get(name, default)
    
    def get_str(self, name: str, default: str = "") -> str:
        """Get environment variable as string."""
        value = self._vars.get(name, default)
        return str(value) if value is not None else default
    
    def get_int(self, name: str, default: int = 0) -> int:
        """Get environment variable as integer."""
        value = self._vars.get(name, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def get_bool(self, name: str, default: bool = False) -> bool:
        """Get environment variable as boolean."""
        value = self._vars.get(name, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value) if value is not None else default
    
    def get_list(self, name: str, default: Optional[List[str]] = None) -> List[str]:
        """Get environment variable as list."""
        value = self._vars.get(name, default)
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            return [v.strip() for v in value.split(',')] if value else []
        return default or []
    
    def set(self, name: str, value: Any) -> None:
        """Set environment variable value."""
        self._vars[name] = value
        os.environ[name] = str(value)
    
    def is_set(self, name: str) -> bool:
        """Check if environment variable is set."""
        return name in self._vars and self._vars[name] is not None
    
    def validate_required(self) -> List[str]:
        """Validate that all required environment variables are set."""
        missing = []
        for env_var in self.DEFINED_VARS:
            if env_var.required and not self.is_set(env_var.name):
                missing.append(env_var.name)
        return missing
    
    def export_to_dict(self) -> Dict[str, Any]:
        """Export all variables to dictionary."""
        return self._vars.copy()
    
    def print_summary(self) -> None:
        """Print summary of current environment configuration."""
        print("\n=== HOLOGIX Environment Configuration ===\n")
        for env_var in self.DEFINED_VARS:
            value = self._vars.get(env_var.name, env_var.default)
            status = "✓" if self.is_set(env_var.name) else "○"
            print(f"{status} {env_var.name}: {value}")
        print()
    
    @classmethod
    def ensure_directories(cls) -> None:
        """Ensure all directories from environment variables exist."""
        env = cls()
        
        dir_vars = [
            "HOLOGIX_MODELS_DIR",
            "HOLOGIX_CACHE_DIR",
        ]
        
        # Add database directory
        db_path = env.get_str("HOLOGIX_DB_PATH")
        if db_path:
            dir_vars.append("HOLOGIX_DB_PATH")
        
        for var_name in dir_vars:
            path_str = env.get_str(var_name)
            if path_str:
                path = Path(path_str).expanduser()
                if var_name == "HOLOGIX_DB_PATH":
                    path = path.parent
                path.mkdir(parents=True, exist_ok=True)


# Global environment manager instance
env_manager = EnvManager()
