"""
HOLOGIX Exception Framework
Custom exceptions for API, engine, and core subsystems.
"""
from typing import Optional, Any, Dict


class HologixError(Exception):
    """Base exception for all HOLOGIX errors."""
    
    def __init__(
        self,
        message: str,
        code: str = "HOLOGIX_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


# =============================================================================
# Configuration Errors
# =============================================================================

class ConfigError(HologixError):
    """Configuration-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="CONFIG_ERROR", details=details)


class ConfigNotFoundError(ConfigError):
    """Configuration file not found."""
    
    def __init__(self, path: str):
        super().__init__(
            f"Configuration file not found: {path}",
            details={"path": path},
        )


class ConfigValidationError(ConfigError):
    """Invalid configuration values."""
    
    def __init__(self, field: str, value: Any, reason: str):
        super().__init__(
            f"Invalid configuration value for '{field}': {reason}",
            details={"field": field, "value": value, "reason": reason},
        )


# =============================================================================
# Authentication & Security Errors
# =============================================================================

class AuthError(HologixError):
    """Authentication-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="AUTH_ERROR", details=details)


class InvalidAPIKeyError(AuthError):
    """Invalid or missing API key."""
    
    def __init__(self):
        super().__init__("Invalid or missing API key")


class ExpiredAPIKeyError(AuthError):
    """API key has expired."""
    
    def __init__(self, key_id: str):
        super().__init__(
            "API key has expired",
            details={"key_id": key_id},
        )


class RateLimitExceededError(AuthError):
    """Rate limit exceeded for API key."""
    
    def __init__(self, limit: int, retry_after: int):
        super().__init__(
            "Rate limit exceeded",
            details={"limit": limit, "retry_after_seconds": retry_after},
        )


# =============================================================================
# Model Management Errors
# =============================================================================

class ModelError(HologixError):
    """Model-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="MODEL_ERROR", details=details)


class ModelNotFoundError(ModelError):
    """Requested model not found."""
    
    def __init__(self, model_name: str):
        super().__init__(
            f"Model not found: {model_name}",
            details={"model_name": model_name},
        )


class ModelLoadError(ModelError):
    """Failed to load model."""
    
    def __init__(self, model_name: str, reason: str):
        super().__init__(
            f"Failed to load model '{model_name}': {reason}",
            details={"model_name": model_name, "reason": reason},
        )


class ModelDownloadError(ModelError):
    """Failed to download model."""
    
    def __init__(self, model_name: str, url: str, reason: str):
        super().__init__(
            f"Failed to download model '{model_name}' from {url}: {reason}",
            details={"model_name": model_name, "url": url, "reason": reason},
        )


class ModelValidationError(ModelError):
    """Model manifest validation failed."""
    
    def __init__(self, model_name: str, errors: list[str]):
        super().__init__(
            f"Model validation failed for '{model_name}'",
            details={"model_name": model_name, "validation_errors": errors},
        )


# =============================================================================
# Inference Errors
# =============================================================================

class InferenceError(HologixError):
    """Inference-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="INFERENCE_ERROR", details=details)


class ContextLengthExceededError(InferenceError):
    """Input exceeds model context length."""
    
    def __init__(self, input_length: int, max_length: int):
        super().__init__(
            "Input tokens exceed maximum context length",
            details={
                "input_length": input_length,
                "max_length": max_length,
            },
        )


class TokenGenerationError(InferenceError):
    """Failed to generate tokens."""
    
    def __init__(self, reason: str):
        super().__init__(
            f"Token generation failed: {reason}",
            details={"reason": reason},
        )


class EngineNotReadyError(InferenceError):
    """Inference engine is not initialized."""
    
    def __init__(self):
        super().__init__("Inference engine is not ready")


# =============================================================================
# Job Queue Errors
# =============================================================================

class JobError(HologixError):
    """Job queue-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="JOB_ERROR", details=details)


class JobNotFoundError(JobError):
    """Requested job not found."""
    
    def __init__(self, job_id: str):
        super().__init__(
            f"Job not found: {job_id}",
            details={"job_id": job_id},
        )


class JobTimeoutError(JobError):
    """Job execution timed out."""
    
    def __init__(self, job_id: str, timeout_seconds: int):
        super().__init__(
            f"Job '{job_id}' timed out after {timeout_seconds} seconds",
            details={"job_id": job_id, "timeout_seconds": timeout_seconds},
        )


class JobCancelledError(JobError):
    """Job was cancelled."""
    
    def __init__(self, job_id: str):
        super().__init__(
            f"Job '{job_id}' was cancelled",
            details={"job_id": job_id},
        )


# =============================================================================
# Storage & Artifact Errors
# =============================================================================

class StorageError(HologixError):
    """Storage-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="STORAGE_ERROR", details=details)


class ArtifactNotFoundError(StorageError):
    """Requested artifact not found."""
    
    def __init__(self, artifact_id: str):
        super().__init__(
            f"Artifact not found: {artifact_id}",
            details={"artifact_id": artifact_id},
        )


class ArtifactWriteError(StorageError):
    """Failed to write artifact."""
    
    def __init__(self, path: str, reason: str):
        super().__init__(
            f"Failed to write artifact to {path}: {reason}",
            details={"path": path, "reason": reason},
        )


class DiskSpaceError(StorageError):
    """Insufficient disk space."""
    
    def __init__(self, required_gb: float, available_gb: float):
        super().__init__(
            "Insufficient disk space",
            details={
                "required_gb": required_gb,
                "available_gb": available_gb,
            },
        )


# =============================================================================
# Engine & Hardware Errors
# =============================================================================

class EngineError(HologixError):
    """C++ engine-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="ENGINE_ERROR", details=details)


class MemoryError(HologixError):
    """Memory allocation/management errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="MEMORY_ERROR", details=details)


class OutOfMemoryError(MemoryError):
    """Out of memory."""
    
    def __init__(self, required_mb: int, available_mb: int):
        super().__init__(
            "Out of memory",
            details={
                "required_mb": required_mb,
                "available_mb": available_mb,
            },
        )


class HardwareError(HologixError):
    """Hardware detection/compatibility errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="HARDWARE_ERROR", details=details)


class UnsupportedHardwareError(HardwareError):
    """Unsupported hardware configuration."""
    
    def __init__(self, component: str, details_msg: str):
        super().__init__(
            f"Unsupported hardware: {component} - {details_msg}",
            details={"component": component},
        )
