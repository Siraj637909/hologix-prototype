"""
HOLOGIX Core Module
Foundation components for the HOLOGIX platform.
"""
from hologix_core.constants import EnvManager, env, get_env
from hologix_core.logger import get_logger, setup_logging
from hologix_core.exceptions import (
    HologixError,
    ConfigError,
    AuthError,
    InvalidAPIKeyError,
    ModelError,
    ModelNotFoundError,
    InferenceError,
    JobError,
    StorageError,
    EngineError,
    MemoryError,
    HardwareError,
)
from hologix_core.database import (
    db_manager,
    get_db,
    get_session,
)
from hologix_core.jobs import (
    job_queue,
    get_job_queue,
    JobStatus,
)
from hologix_core.artifacts import (
    artifact_manager,
    get_artifact_manager,
)

__all__ = [
    # Environment
    "EnvManager",
    "env",
    "get_env",
    # Logging
    "get_logger",
    "setup_logging",
    # Database
    "db_manager",
    "get_db",
    "get_session",
    # Jobs
    "job_queue",
    "get_job_queue",
    "JobStatus",
    # Artifacts
    "artifact_manager",
    "get_artifact_manager",
    # Exceptions
    "HologixError",
    "ConfigError",
    "AuthError",
    "InvalidAPIKeyError",
    "ModelError",
    "ModelNotFoundError",
    "InferenceError",
    "JobError",
    "StorageError",
    "EngineError",
    "MemoryError",
    "HardwareError",
]
