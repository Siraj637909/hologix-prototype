"""
HOLOGIX Exception Framework

Production-grade exception handling with custom exception classes,
error responses, and centralized exception middleware.
"""

from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
import traceback
import sys


@dataclass
class ErrorDetail:
    """Detailed error information."""
    code: int
    message: str
    details: Optional[Dict[str, Any]] = None
    traceback: Optional[str] = None


class HologixException(Exception):
    """Base exception for all HOLOGIX exceptions."""
    
    error_code: int = 1000
    status_code: int = 500
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        include_traceback: bool = False,
    ):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.include_traceback = include_traceback
        
        if include_traceback:
            self.traceback_str = traceback.format_exc()
        else:
            self.traceback_str = None
    
    def to_error_detail(self) -> ErrorDetail:
        """Convert to ErrorDetail object."""
        return ErrorDetail(
            code=self.error_code,
            message=self.message,
            details=self.details,
            traceback=self.traceback_str,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        result = {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "type": self.__class__.__name__,
            }
        }
        
        if self.details:
            result["error"]["details"] = self.details
        
        if self.traceback_str:
            result["error"]["traceback"] = self.traceback_str
        
        return result


class AuthenticationError(HologixException):
    """Authentication failed."""
    error_code = 1001
    status_code = 401


class AuthorizationError(HologixException):
    """Authorization failed (insufficient permissions)."""
    error_code = 1002
    status_code = 403


class RateLimitError(HologixException):
    """Rate limit exceeded."""
    error_code = 1003
    status_code = 429
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, details)
        self.retry_after = retry_after
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        if self.retry_after is not None:
            result["error"]["retry_after"] = self.retry_after
        return result


class ModelNotFoundError(HologixException):
    """Requested model not found."""
    error_code = 1004
    status_code = 404


class ModelLoadError(HologixException):
    """Failed to load model."""
    error_code = 1005
    status_code = 500


class InvalidRequestError(HologixException):
    """Invalid request parameters."""
    error_code = 1006
    status_code = 400


class ValidationError(HologixException):
    """Request validation failed."""
    error_code = 1007
    status_code = 422
    
    def __init__(
        self,
        message: str = "Validation failed",
        field_errors: Optional[List[Dict[str, Any]]] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, details)
        self.field_errors = field_errors or []
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        if self.field_errors:
            result["error"]["field_errors"] = self.field_errors
        return result


class TimeoutError(HologixException):
    """Request timeout."""
    error_code = 1008
    status_code = 408


class QueueFullError(HologixException):
    """Job queue is full."""
    error_code = 1009
    status_code = 503


class DiskSpaceError(HologixException):
    """Insufficient disk space."""
    error_code = 1010
    status_code = 507


class UnsupportedFormatError(HologixException):
    """Unsupported file or model format."""
    error_code = 1011
    status_code = 415


class HardwareIncompatibleError(HologixException):
    """Hardware incompatibility detected."""
    error_code = 1012
    status_code = 500


class ConfigurationError(HologixException):
    """Configuration error."""
    error_code = 1013
    status_code = 500


class DownloadError(HologixException):
    """Model download failed."""
    error_code = 1014
    status_code = 500
    
    def __init__(
        self,
        message: str = "Download failed",
        url: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, details)
        self.url = url
        self.http_status_code = status_code
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        if self.url:
            result["error"]["url"] = self.url
        if self.http_status_code:
            result["error"]["http_status_code"] = self.http_status_code
        return result


class InferenceError(HologixException):
    """Inference execution failed."""
    error_code = 1015
    status_code = 500


class EngineNotInitializedError(HologixException):
    """Inference engine not initialized."""
    error_code = 1016
    status_code = 503


class ResourceExhaustedError(HologixException):
    """System resources exhausted (RAM, VRAM, etc.)."""
    error_code = 1017
    status_code = 507


class NetworkError(HologixException):
    """Network operation failed."""
    error_code = 1018
    status_code = 502


class FilesystemError(HologixException):
    """Filesystem operation failed."""
    error_code = 1019
    status_code = 500


class DatabaseError(HologixException):
    """Database operation failed."""
    error_code = 1020
    status_code = 500


class CacheError(HologixException):
    """Cache operation failed."""
    error_code = 1021
    status_code = 500


class StreamError(HologixException):
    """Streaming operation failed."""
    error_code = 1022
    status_code = 500


class ExceptionHandler:
    """
    Centralized exception handler.
    
    Provides utilities for handling, logging, and formatting exceptions.
    """
    
    EXCEPTION_MAPPING = {
        AuthenticationError: 401,
        AuthorizationError: 403,
        RateLimitError: 429,
        ModelNotFoundError: 404,
        ModelLoadError: 500,
        InvalidRequestError: 400,
        ValidationError: 422,
        TimeoutError: 408,
        QueueFullError: 503,
        DiskSpaceError: 507,
        UnsupportedFormatError: 415,
        HardwareIncompatibleError: 500,
        ConfigurationError: 500,
        DownloadError: 500,
        InferenceError: 500,
        EngineNotInitializedError: 503,
        ResourceExhaustedError: 507,
        NetworkError: 502,
        FilesystemError: 500,
        DatabaseError: 500,
        CacheError: 500,
        StreamError: 500,
    }
    
    @classmethod
    def get_status_code(cls, exception: Exception) -> int:
        """Get HTTP status code for an exception."""
        if isinstance(exception, HologixException):
            return exception.status_code
        
        for exc_class, status_code in cls.EXCEPTION_MAPPING.items():
            if isinstance(exception, exc_class):
                return status_code
        
        return 500
    
    @classmethod
    def handle_exception(
        cls,
        exception: Exception,
        include_traceback: bool = False,
        log_exception: bool = True,
    ) -> Dict[str, Any]:
        """
        Handle an exception and return formatted error response.
        
        Args:
            exception: The exception to handle
            include_traceback: Include stack trace in response
            log_exception: Log the exception
            
        Returns:
            Formatted error dictionary
        """
        if log_exception:
            import logging
            logger = logging.getLogger("hologix")
            logger.exception(f"Exception occurred: {exception}")
        
        if isinstance(exception, HologixException):
            return exception.to_dict()
        
        # Generic exception handling
        error_response = {
            "error": {
                "code": 1000,
                "message": str(exception),
                "type": exception.__class__.__name__,
            }
        }
        
        if include_traceback:
            error_response["error"]["traceback"] = traceback.format_exc()
        
        return error_response
    
    @classmethod
    def create_error_response(
        cls,
        message: str,
        code: int = 1000,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a standardized error response."""
        return {
            "error": {
                "code": code,
                "message": message,
                "details": details,
            }
        }


def raise_from_exception(
    exception: Exception,
    default_exception: type = HologixException,
) -> None:
    """Raise a HOLOGIX exception from a generic exception."""
    if isinstance(exception, HologixException):
        raise exception
    
    raise default_exception(
        message=str(exception),
        include_traceback=True,
    )


def safe_execute(func, *args, **kwargs):
    """
    Execute a function safely and return (success, result/error).
    
    Returns:
        Tuple of (success: bool, result_or_error)
    """
    try:
        return True, func(*args, **kwargs)
    except Exception as e:
        return False, e
