"""
HOLOGIX Logger Framework
Production-grade structured logging with file rotation and JSON output support.
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import json

from hologix_core.constants.env_manager import env


class ColoredFormatter(logging.Formatter):
    """Console formatter with color-coded log levels."""
    
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured log output."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


class HologixLogger:
    """Centralized logger manager for HOLOGIX."""
    
    _instance: Optional["HologixLogger"] = None
    _loggers: dict[str, logging.Logger] = {}
    
    def __new__(cls) -> "HologixLogger":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        if self._initialized:
            return
        
        self.log_dir = env.LOGS_DIR
        self.debug_mode = env.debug_mode
        
        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self._setup_root_logger()
        self._initialized = True
    
    def _setup_root_logger(self) -> None:
        """Configure the root logger with console and file handlers."""
        root_logger = logging.getLogger("hologix")
        root_logger.setLevel(logging.DEBUG if self.debug_mode else logging.INFO)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler with colored output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG if self.debug_mode else logging.INFO)
        console_formatter = ColoredFormatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # File handler with daily rotation
        log_file = self.log_dir / f"hologix_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        # JSON log file for machine parsing
        json_log_file = self.log_dir / f"hologix_{datetime.now().strftime('%Y%m%d')}.jsonl"
        json_handler = logging.FileHandler(json_log_file, encoding="utf-8")
        json_handler.setLevel(logging.INFO)
        json_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(json_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a named logger instance."""
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(f"hologix.{name}")
        return self._loggers[name]
    
    def set_level(self, level: int | str) -> None:
        """Set the global log level."""
        if isinstance(level, str):
            level = getattr(logging, level.upper(), logging.INFO)
        logging.getLogger("hologix").setLevel(level)
        
        for handler in logging.getLogger("hologix").handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setLevel(level)


def get_logger(name: str = "hologix") -> logging.Logger:
    """Get a logger instance with the specified name."""
    logger_manager = HologixLogger()
    return logger_manager.get_logger(name)


def setup_logging(level: Optional[int | str] = None) -> None:
    """Initialize the logging system."""
    logger_manager = HologixLogger()
    if level is not None:
        logger_manager.set_level(level)


# Initialize default logger on module import
setup_logging()
