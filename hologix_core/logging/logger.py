"""
HOLOGIX Logging System

Production-grade logging framework with file rotation, structured logging, and async support.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import json
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        if hasattr(record, 'request_id'):
            log_data["request_id"] = record.request_id
        
        if hasattr(record, 'user_id'):
            log_data["user_id"] = record.user_id
        
        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Colored console formatter for better readability."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


class HologixLogger:
    """
    HOLOGIX production logger.
    
    Provides centralized logging with:
    - Console and file output
    - Log rotation
    - Structured JSON logging option
    - Request context injection
    """
    
    _instances: Dict[str, logging.Logger] = {}
    _default_logger: Optional[logging.Logger] = None
    
    @classmethod
    def setup(
        cls,
        name: str = "hologix",
        level: str = "INFO",
        log_file: Optional[str] = None,
        max_bytes: int = 52428800,  # 50MB
        backup_count: int = 5,
        use_json: bool = False,
        console_output: bool = True,
    ) -> logging.Logger:
        """
        Set up a logger with the specified configuration.
        
        Args:
            name: Logger name
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Path to log file (optional)
            max_bytes: Maximum log file size before rotation
            backup_count: Number of backup files to keep
            use_json: Use JSON formatting
            console_output: Enable console output
            
        Returns:
            Configured logger instance
        """
        if name in cls._instances:
            return cls._instances[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        logger.handlers.clear()
        
        # Create formatter
        if use_json:
            formatter = JSONFormatter()
        else:
            format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            if console_output:
                formatter = ColoredFormatter(format_str)
            else:
                formatter = logging.Formatter(format_str)
        
        # Console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # File handler with rotation
        if log_file:
            log_path = Path(log_file).expanduser()
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=max_bytes,
                backupCount=backup_count,
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        cls._instances[name] = logger
        
        if cls._default_logger is None:
            cls._default_logger = logger
        
        return logger
    
    @classmethod
    def get_logger(cls, name: Optional[str] = None) -> logging.Logger:
        """Get a logger instance by name or return the default logger."""
        if name is None:
            if cls._default_logger is None:
                return cls.setup()
            return cls._default_logger
        
        if name in cls._instances:
            return cls._instances[name]
        
        return cls.setup(name=name)
    
    @classmethod
    def inject_context(cls, logger: logging.Logger, **context: Any) -> logging.Logger:
        """Inject context into logger for structured logging."""
        class ContextAdapter(logging.LoggerAdapter):
            def process(self, msg, kwargs):
                extra = kwargs.get('extra', {})
                extra.update(context)
                kwargs['extra'] = extra
                return msg, kwargs
        
        return ContextAdapter(logger, context)
    
    @classmethod
    def set_level(cls, level: str, name: Optional[str] = None) -> None:
        """Set logging level for a logger."""
        logger = cls.get_logger(name)
        logger.setLevel(getattr(logging, level.upper()))
        
        for handler in logger.handlers:
            handler.setLevel(getattr(logging, level.upper()))
    
    @classmethod
    def shutdown(cls) -> None:
        """Shutdown all loggers and handlers."""
        for logger in cls._instances.values():
            for handler in logger.handlers:
                handler.close()
            logger.handlers.clear()
        cls._instances.clear()
        cls._default_logger = None


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Convenience function to get a logger."""
    return HologixLogger.get_logger(name)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    use_json: bool = False,
) -> logging.Logger:
    """Convenience function to set up the default logger."""
    return HologixLogger.setup(
        name="hologix",
        level=level,
        log_file=log_file,
        use_json=use_json,
    )


# Initialize default logger on module load
logger = setup_logging()
