"""
HOLOGIX Database Layer
SQLite database models and session management using SQLAlchemy.
"""
from datetime import datetime
from typing import Optional, List, Any
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    Float,
    Text,
    ForeignKey,
    Index,
    event,
)
from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
    relationship,
    Session,
)
from sqlalchemy.pool import StaticPool

from hologix_core.constants.env_manager import env
from hologix_core.logger import get_logger

logger = get_logger("database")
Base = declarative_base()


# =============================================================================
# Database Models
# =============================================================================

class APIKey(Base):
    """API key storage for authentication."""
    
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key_hash = Column(String(64), unique=True, nullable=False, index=True)
    key_prefix = Column(String(16), nullable=False)  # First chars for identification
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    
    # Usage tracking
    total_requests = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    
    # Rate limiting
    requests_this_minute = Column(Integer, default=0, nullable=False)
    minute_reset_at = Column(DateTime, nullable=True)
    
    # Relationships
    usage_logs = relationship("UsageLog", back_populates="api_key", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_api_key_active", "is_active", "expires_at"),
    )
    
    def __repr__(self) -> str:
        return f"<APIKey(id={self.id}, prefix='{self.key_prefix}', active={self.is_active})>"


class Model(Base):
    """Local model registry."""
    
    __tablename__ = "models"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    path = Column(String(1024), nullable=False)
    manifest_path = Column(String(1024), nullable=True)
    
    # Model metadata
    model_type = Column(String(64), nullable=False)  # llm, embedding, etc.
    architecture = Column(String(128), nullable=True)  # llama, mistral, etc.
    parameter_count = Column(Integer, nullable=True)  # In millions
    quantization = Column(String(32), nullable=True)  # q4_0, q8_0, f16, etc.
    context_length = Column(Integer, nullable=True)
    
    # Download info
    source_url = Column(String(1024), nullable=True)
    source_type = Column(String(32), nullable=True)  # huggingface, local, etc.
    
    # Status
    is_downloaded = Column(Boolean, default=False, nullable=False)
    download_progress = Column(Float, default=0.0, nullable=False)
    downloaded_at = Column(DateTime, nullable=True)
    last_accessed_at = Column(DateTime, nullable=True)
    
    # Cache info
    size_bytes = Column(Integer, default=0, nullable=False)
    checksum = Column(String(64), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index("idx_model_type", "model_type", "is_downloaded"),
    )
    
    def __repr__(self) -> str:
        return f"<Model(name='{self.name}', type='{self.model_type}', downloaded={self.is_downloaded})>"


class Job(Base):
    """Async job queue for inference tasks."""
    
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(64), unique=True, nullable=False, index=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=True)
    
    # Job details
    job_type = Column(String(64), nullable=False)  # chat, completion, embedding, etc.
    model_name = Column(String(255), nullable=False)
    status = Column(String(32), default="pending", nullable=False, index=True)  # pending, running, completed, failed, cancelled
    
    # Request data
    request_data = Column(Text, nullable=True)  # JSON serialized
    
    # Response data
    response_data = Column(Text, nullable=True)  # JSON serialized
    error_message = Column(Text, nullable=True)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Progress
    progress_percent = Column(Float, default=0.0, nullable=False)
    
    # Relationships
    api_key = relationship("APIKey", back_populates="jobs")
    artifacts = relationship("Artifact", back_populates="job", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_job_status_created", "status", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Job(job_id='{self.job_id}', status='{self.status}', type='{self.job_type}')>"


class Artifact(Base):
    """Output artifacts from jobs (images, audio, files, etc.)."""
    
    __tablename__ = "artifacts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    artifact_id = Column(String(64), unique=True, nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    
    # Artifact info
    name = Column(String(255), nullable=False)
    file_path = Column(String(1024), nullable=False)
    file_type = Column(String(64), nullable=False)  # image/png, audio/wav, etc.
    size_bytes = Column(Integer, default=0, nullable=False)
    
    # Metadata
    metadata = Column(Text, nullable=True)  # JSON serialized
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    job = relationship("Job", back_populates="artifacts")
    
    def __repr__(self) -> str:
        return f"<Artifact(artifact_id='{self.artifact_id}', name='{self.name}')>"


class UsageLog(Base):
    """API usage tracking and analytics."""
    
    __tablename__ = "usage_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=False)
    
    # Request info
    endpoint = Column(String(255), nullable=False)
    method = Column(String(16), nullable=False)
    model_name = Column(String(255), nullable=True)
    
    # Token usage
    prompt_tokens = Column(Integer, default=0, nullable=False)
    completion_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    
    # Timing
    latency_ms = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Status
    status_code = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    api_key = relationship("APIKey", back_populates="usage_logs")
    
    __table_args__ = (
        Index("idx_usage_timestamp", "timestamp", "api_key_id"),
        Index("idx_usage_model", "model_name", "timestamp"),
    )
    
    def __repr__(self) -> str:
        return f"<UsageLog(api_key_id={self.api_key_id}, tokens={self.total_tokens}, endpoint='{self.endpoint}')>"


class Settings(Base):
    """Application settings stored in database."""
    
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(255), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    value_type = Column(String(32), default="string", nullable=False)  # string, int, float, bool, json
    
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<Settings(key='{self.key}', value='{self.value[:50]}...')>"


# =============================================================================
# Database Manager
# =============================================================================

class DatabaseManager:
    """Manages database connections and sessions."""
    
    _instance: Optional["DatabaseManager"] = None
    _engine = None
    _session_factory = None
    
    def __new__(cls) -> "DatabaseManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        if self._initialized:
            return
        
        self.db_path = env.DB_PATH
        self._initialize()
        self._initialized = True
    
    def _initialize(self) -> None:
        """Initialize database engine and create tables."""
        logger.info(f"Initializing database at {self.db_path}")
        
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create engine with SQLite-specific settings
        self._engine = create_engine(
            f"sqlite:///{self.db_path}",
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
            echo=False,
        )
        
        # Create all tables
        Base.metadata.create_all(self._engine)
        
        # Create session factory
        self._session_factory = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
        
        logger.info("Database initialized successfully")
    
    def get_session(self) -> Session:
        """Get a new database session."""
        return self._session_factory()
    
    def close(self) -> None:
        """Close database connections."""
        if self._engine:
            self._engine.dispose()
            logger.info("Database connections closed")


# =============================================================================
# Global Instance
# =============================================================================

def get_db() -> DatabaseManager:
    """Get the global database manager instance."""
    return DatabaseManager()


def get_session() -> Session:
    """Get a new database session from the global manager."""
    return DatabaseManager().get_session()


# Initialize database on module import
db_manager = DatabaseManager()
