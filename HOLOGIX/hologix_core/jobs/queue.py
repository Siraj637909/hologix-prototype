"""
HOLOGIX Async Job Queue
Production-grade async job queue for inference tasks with SQLite backend.
"""
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable, Awaitable
from enum import Enum

from sqlalchemy import select, update, delete
from sqlalchemy.orm import Session

from hologix_core.database.models import Job, APIKey
from hologix_core.database import get_session, db_manager
from hologix_core.logger import get_logger
from hologix_core.exceptions import JobNotFoundError, JobCancelledError, JobTimeoutError

logger = get_logger("job_queue")


class JobStatus(str, Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobQueue:
    """Async job queue manager for inference tasks."""
    
    _instance: Optional["JobQueue"] = None
    _workers: Dict[str, asyncio.Task] = {}
    _handlers: Dict[str, Callable] = {}
    
    def __new__(cls) -> "JobQueue":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        if self._initialized:
            return
        
        self._queue: asyncio.Queue = asyncio.Queue()
        self._max_workers = 4
        self._default_timeout_seconds = 300
        self._poll_interval_seconds = 1.0
        
        self._initialized = True
        logger.info("Job queue initialized")
    
    def register_handler(
        self,
        job_type: str,
        handler: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]],
    ) -> None:
        """Register a handler function for a specific job type."""
        self._handlers[job_type] = handler
        logger.info(f"Registered handler for job type: {job_type}")
    
    async def submit_job(
        self,
        job_type: str,
        model_name: str,
        request_data: Dict[str, Any],
        api_key_id: Optional[int] = None,
        priority: int = 0,
    ) -> str:
        """Submit a new job to the queue."""
        job_id = f"job_{uuid.uuid4().hex}"
        
        with get_session() as session:
            job = Job(
                job_id=job_id,
                api_key_id=api_key_id,
                job_type=job_type,
                model_name=model_name,
                status=JobStatus.PENDING.value,
                request_data=json.dumps(request_data),
                progress_percent=0.0,
            )
            session.add(job)
            session.commit()
        
        # Add to processing queue
        await self._queue.put((priority, job_id))
        
        logger.info(f"Submitted job {job_id} (type={job_type}, model={model_name})")
        return job_id
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get current job status and details."""
        with get_session() as session:
            stmt = select(Job).where(Job.job_id == job_id)
            job = session.execute(stmt).scalar_one_or_none()
            
            if not job:
                return None
            
            return {
                "job_id": job.job_id,
                "job_type": job.job_type,
                "model_name": job.model_name,
                "status": job.status,
                "progress_percent": job.progress_percent,
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "error_message": job.error_message,
                "response_data": json.loads(job.response_data) if job.response_data else None,
            }
    
    async def wait_for_job(
        self,
        job_id: str,
        timeout_seconds: Optional[int] = None,
        poll_interval: float = 1.0,
    ) -> Dict[str, Any]:
        """Wait for a job to complete and return results."""
        timeout = timeout_seconds or self._default_timeout_seconds
        start_time = datetime.utcnow()
        
        while True:
            # Check timeout
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed > timeout:
                raise JobTimeoutError(job_id, timeout)
            
            # Get job status
            job_info = await self.get_job_status(job_id)
            
            if not job_info:
                raise JobNotFoundError(job_id)
            
            if job_info["status"] == JobStatus.COMPLETED.value:
                return job_info
            
            if job_info["status"] == JobStatus.FAILED.value:
                raise Exception(f"Job failed: {job_info.get('error_message', 'Unknown error')}")
            
            if job_info["status"] == JobStatus.CANCELLED.value:
                raise JobCancelledError(job_id)
            
            # Wait before polling again
            await asyncio.sleep(poll_interval)
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending or running job."""
        with get_session() as session:
            stmt = (
                update(Job)
                .where(Job.job_id == job_id)
                .values(
                    status=JobStatus.CANCELLED.value,
                    completed_at=datetime.utcnow(),
                )
            )
            result = session.execute(stmt)
            session.commit()
            
            cancelled = result.rowcount > 0
            if cancelled:
                logger.info(f"Cancelled job {job_id}")
            
            return cancelled
    
    async def _process_job(self, job_id: str) -> None:
        """Process a single job from the queue."""
        with get_session() as session:
            # Get job from database
            stmt = select(Job).where(Job.job_id == job_id)
            job = session.execute(stmt).scalar_one_or_none()
            
            if not job:
                logger.warning(f"Job {job_id} not found, skipping")
                return
            
            # Check if still pending
            if job.status != JobStatus.PENDING.value:
                logger.debug(f"Job {job_id} is not pending (status={job.status}), skipping")
                return
            
            # Check for handler
            handler = self._handlers.get(job.job_type)
            if not handler:
                logger.error(f"No handler registered for job type: {job.job_type}")
                job.status = JobStatus.FAILED.value
                job.error_message = f"No handler for job type: {job.job_type}"
                job.completed_at = datetime.utcnow()
                session.commit()
                return
            
            # Update to running
            job.status = JobStatus.RUNNING.value
            job.started_at = datetime.utcnow()
            session.commit()
        
        try:
            logger.info(f"Processing job {job_id} (type={job.job_type})")
            
            # Parse request data
            request_data = json.loads(job.request_data) if job.request_data else {}
            
            # Execute handler
            result = await handler(request_data)
            
            # Update job as completed
            with get_session() as session:
                stmt = (
                    update(Job)
                    .where(Job.job_id == job_id)
                    .values(
                        status=JobStatus.COMPLETED.value,
                        response_data=json.dumps(result),
                        progress_percent=100.0,
                        completed_at=datetime.utcnow(),
                    )
                )
                session.execute(stmt)
                session.commit()
            
            logger.info(f"Job {job_id} completed successfully")
            
        except Exception as e:
            logger.exception(f"Job {job_id} failed with error: {e}")
            
            with get_session() as session:
                stmt = (
                    update(Job)
                    .where(Job.job_id == job_id)
                    .values(
                        status=JobStatus.FAILED.value,
                        error_message=str(e),
                        completed_at=datetime.utcnow(),
                    )
                )
                session.execute(stmt)
                session.commit()
    
    async def _worker(self, worker_id: str) -> None:
        """Worker coroutine that processes jobs from the queue."""
        logger.info(f"Worker {worker_id} started")
        
        while True:
            try:
                # Get next job from queue
                priority, job_id = await self._queue.get()
                
                # Process the job
                await self._process_job(job_id)
                
                # Mark task as done
                self._queue.task_done()
                
            except asyncio.CancelledError:
                logger.info(f"Worker {worker_id} cancelled")
                break
            except Exception as e:
                logger.exception(f"Worker {worker_id} error: {e}")
    
    async def start_workers(self, num_workers: Optional[int] = None) -> None:
        """Start background workers to process jobs."""
        num_workers = num_workers or self._max_workers
        
        for i in range(num_workers):
            worker_id = f"worker_{i}"
            if worker_id not in self._workers:
                task = asyncio.create_task(self._worker(worker_id))
                self._workers[worker_id] = task
                logger.info(f"Started worker {worker_id}")
    
    async def stop_workers(self) -> None:
        """Stop all background workers."""
        for worker_id, task in self._workers.items():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self._workers.clear()
        logger.info("All workers stopped")
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        with get_session() as session:
            # Count jobs by status
            stats = {"pending": 0, "running": 0, "completed": 0, "failed": 0, "cancelled": 0}
            
            for status in JobStatus:
                stmt = select(Job).where(Job.status == status.value)
                count = len(session.execute(stmt).scalars().all())
                stats[status.value] = count
            
            return {
                "queue_size": self._queue.qsize(),
                "active_workers": len(self._workers),
                "jobs_by_status": stats,
                "registered_handlers": list(self._handlers.keys()),
            }


# =============================================================================
# Global Instance
# =============================================================================

def get_job_queue() -> JobQueue:
    """Get the global job queue instance."""
    return JobQueue()


job_queue = JobQueue()
