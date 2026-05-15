"""
HOLOGIX Artifact Manager
Manages output artifacts (images, audio, files) from inference jobs.
"""
import hashlib
import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from sqlalchemy import select, delete as sql_delete
from sqlalchemy.orm import Session

from hologix_core.constants.env_manager import env
from hologix_core.database.models import Artifact, Job
from hologix_core.database import get_session
from hologix_core.logger import get_logger
from hologix_core.exceptions import (
    ArtifactNotFoundError,
    ArtifactWriteError,
    DiskSpaceError,
)

logger = get_logger("artifacts")


class ArtifactManager:
    """Manages storage and retrieval of output artifacts."""
    
    _instance: Optional["ArtifactManager"] = None
    
    def __new__(cls) -> "ArtifactManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        if self._initialized:
            return
        
        self.artifacts_dir = env.ARTIFACTS_DIR
        self.max_storage_gb = 10.0  # Default max storage
        
        self._initialized = True
        logger.info(f"Artifact manager initialized at {self.artifacts_dir}")
    
    def _check_disk_space(self, required_bytes: int) -> bool:
        """Check if there's enough disk space for the artifact."""
        try:
            stat = shutil.disk_usage(self.artifacts_dir)
            available_gb = stat.free / (1024 ** 3)
            required_gb = required_bytes / (1024 ** 3)
            
            if available_gb < required_gb:
                raise DiskSpaceError(required_gb, available_gb)
            
            return True
        except DiskSpaceError:
            raise
        except Exception as e:
            logger.warning(f"Could not check disk space: {e}")
            return True  # Proceed if we can't check
    
    def _generate_artifact_id(self) -> str:
        """Generate a unique artifact ID."""
        return f"art_{uuid.uuid4().hex}"
    
    def _compute_checksum(self, file_path: Path) -> str:
        """Compute SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def save_artifact(
        self,
        job_id: int,
        name: str,
        content: bytes,
        file_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Save an artifact to disk and register it in the database."""
        with get_session() as session:
            # Verify job exists
            stmt = select(Job).where(Job.id == job_id)
            job = session.execute(stmt).scalar_one_or_none()
            
            if not job:
                raise ValueError(f"Job with id {job_id} not found")
            
            # Generate artifact ID and path
            artifact_id = self._generate_artifact_id()
            extension = file_type.split("/")[-1] if "/" in file_type else "bin"
            
            # Create dated subdirectory
            date_subdir = datetime.utcnow().strftime("%Y/%m/%d")
            artifact_dir = self.artifacts_dir / date_subdir
            artifact_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = artifact_dir / f"{artifact_id}.{extension}"
            
            # Check disk space
            self._check_disk_space(len(content))
            
            # Write file
            try:
                with open(file_path, "wb") as f:
                    f.write(content)
            except Exception as e:
                raise ArtifactWriteError(str(file_path), str(e))
            
            # Compute checksum
            checksum = self._compute_checksum(file_path)
            
            # Create database record
            artifact = Artifact(
                artifact_id=artifact_id,
                job_id=job_id,
                name=name,
                file_path=str(file_path),
                file_type=file_type,
                size_bytes=len(content),
                metadata=json.dumps(metadata) if metadata else None,
            )
            session.add(artifact)
            session.commit()
            session.refresh(artifact)
            
            logger.info(f"Saved artifact {artifact_id} ({name}, {len(content)} bytes)")
            
            return {
                "artifact_id": artifact.artifact_id,
                "name": artifact.name,
                "file_path": str(file_path),
                "file_type": artifact.file_type,
                "size_bytes": artifact.size_bytes,
                "checksum": checksum,
                "created_at": artifact.created_at.isoformat(),
            }
    
    def save_file_artifact(
        self,
        job_id: int,
        source_path: Path,
        name: Optional[str] = None,
        file_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Save an existing file as an artifact."""
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        name = name or source_path.name
        file_type = file_type or self._guess_mime_type(source_path)
        
        with open(source_path, "rb") as f:
            content = f.read()
        
        return self.save_artifact(
            job_id=job_id,
            name=name,
            content=content,
            file_type=file_type,
            metadata=metadata,
        )
    
    def get_artifact(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """Get artifact metadata without loading content."""
        with get_session() as session:
            stmt = select(Artifact).where(Artifact.artifact_id == artifact_id)
            artifact = session.execute(stmt).scalar_one_or_none()
            
            if not artifact:
                return None
            
            return {
                "artifact_id": artifact.artifact_id,
                "name": artifact.name,
                "file_path": artifact.file_path,
                "file_type": artifact.file_type,
                "size_bytes": artifact.size_bytes,
                "created_at": artifact.created_at.isoformat(),
                "job_id": artifact.job_id,
            }
    
    def load_artifact(self, artifact_id: str) -> Optional[bytes]:
        """Load artifact content from disk."""
        with get_session() as session:
            stmt = select(Artifact).where(Artifact.artifact_id == artifact_id)
            artifact = session.execute(stmt).scalar_one_or_none()
            
            if not artifact:
                return None
            
            file_path = Path(artifact.file_path)
            if not file_path.exists():
                logger.error(f"Artifact file not found: {file_path}")
                return None
            
            with open(file_path, "rb") as f:
                return f.read()
    
    def stream_artifact(self, artifact_id: str):
        """Stream artifact content for large files."""
        with get_session() as session:
            stmt = select(Artifact).where(Artifact.artifact_id == artifact_id)
            artifact = session.execute(stmt).scalar_one_or_none()
            
            if not artifact:
                return None
            
            file_path = Path(artifact.file_path)
            if not file_path.exists():
                return None
            
            def iterfile():
                with open(file_path, "rb") as f:
                    while chunk := f.read(8192):
                        yield chunk
            
            return {
                "iterator": iterfile(),
                "file_type": artifact.file_type,
                "size_bytes": artifact.size_bytes,
                "filename": artifact.name,
            }
    
    def delete_artifact(self, artifact_id: str) -> bool:
        """Delete an artifact from disk and database."""
        with get_session() as session:
            stmt = select(Artifact).where(Artifact.artifact_id == artifact_id)
            artifact = session.execute(stmt).scalar_one_or_none()
            
            if not artifact:
                return False
            
            # Delete file from disk
            file_path = Path(artifact.file_path)
            if file_path.exists():
                try:
                    file_path.unlink()
                    logger.debug(f"Deleted artifact file: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to delete artifact file: {e}")
            
            # Delete from database
            stmt = sql_delete(Artifact).where(Artifact.artifact_id == artifact_id)
            session.execute(stmt)
            session.commit()
            
            logger.info(f"Deleted artifact {artifact_id}")
            return True
    
    def list_artifacts(
        self,
        job_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List artifacts, optionally filtered by job ID."""
        with get_session() as session:
            stmt = select(Artifact)
            
            if job_id is not None:
                stmt = stmt.where(Artifact.job_id == job_id)
            
            stmt = stmt.order_by(Artifact.created_at.desc()).offset(offset).limit(limit)
            
            artifacts = session.execute(stmt).scalars().all()
            
            return [
                {
                    "artifact_id": a.artifact_id,
                    "name": a.name,
                    "file_type": a.file_type,
                    "size_bytes": a.size_bytes,
                    "created_at": a.created_at.isoformat(),
                    "job_id": a.job_id,
                }
                for a in artifacts
            ]
    
    def get_job_artifacts(self, job_id: int) -> List[Dict[str, Any]]:
        """Get all artifacts for a specific job."""
        return self.list_artifacts(job_id=job_id, limit=1000)
    
    def cleanup_old_artifacts(self, days_old: int = 30) -> int:
        """Remove artifacts older than specified days."""
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        deleted_count = 0
        
        with get_session() as session:
            stmt = select(Artifact).where(Artifact.created_at < cutoff_date)
            artifacts = session.execute(stmt).scalars().all()
            
            for artifact in artifacts:
                # Delete file
                file_path = Path(artifact.file_path)
                if file_path.exists():
                    try:
                        file_path.unlink()
                    except Exception as e:
                        logger.error(f"Failed to delete old artifact file: {e}")
                
                # Delete from database
                session.delete(artifact)
                deleted_count += 1
            
            session.commit()
        
        logger.info(f"Cleaned up {deleted_count} artifacts older than {days_old} days")
        return deleted_count
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        total_size = 0
        artifact_count = 0
        
        with get_session() as session:
            stmt = select(Artifact)
            artifacts = session.execute(stmt).scalars().all()
            
            for artifact in artifacts:
                file_path = Path(artifact.file_path)
                if file_path.exists():
                    total_size += file_path.stat().st_size
                    artifact_count += 1
        
        try:
            stat = shutil.disk_usage(self.artifacts_dir)
            total_gb = stat.total / (1024 ** 3)
            used_gb = stat.used / (1024 ** 3)
            available_gb = stat.free / (1024 ** 3)
        except Exception:
            total_gb = used_gb = available_gb = 0.0
        
        return {
            "artifact_count": artifact_count,
            "total_size_bytes": total_size,
            "total_size_gb": total_size / (1024 ** 3),
            "disk_total_gb": total_gb,
            "disk_used_gb": used_gb,
            "disk_available_gb": available_gb,
            "usage_percent": (used_gb / total_gb * 100) if total_gb > 0 else 0,
        }
    
    def _guess_mime_type(self, path: Path) -> str:
        """Guess MIME type from file extension."""
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".ogg": "audio/ogg",
            ".mp4": "video/mp4",
            ".webm": "video/webm",
            ".txt": "text/plain",
            ".json": "application/json",
            ".pdf": "application/pdf",
        }
        return mime_types.get(path.suffix.lower(), "application/octet-stream")


# =============================================================================
# Global Instance
# =============================================================================

def get_artifact_manager() -> ArtifactManager:
    """Get the global artifact manager instance."""
    return ArtifactManager()


artifact_manager = ArtifactManager()
