from app.celery_app import app
from app.database import SessionLocal
from app import models
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.task(bind=True, max_retries=5)
def execute_job(self, job_id: str):
    """Execute a job. Celery handles retries automatically."""
    
    db = SessionLocal()
    
    try:
        # Get job from database
        job = db.query(models.Job).filter(models.Job.job_id == job_id).first()
        
        if not job:
            logger.error(f"Job {job_id} not found")
            return
        
        # Mark as processing
        job.status = models.JobStatus.PROCESSING
        job.started_at = datetime.utcnow()
        job.attempts += 1
        job.worker_id = self.request.hostname
        db.commit()
        
        logger.info(f"Processing job {job_id} (attempt {job.attempts})")
        
        # Parse params
        params = json.loads(job.params)
        
        # Route to appropriate executor
        if job.job_type == "test":
            result = handle_test_job(params)
        else:
            raise ValueError(f"Unknown job type: {job.job_type}")
        
        # Mark as completed
        job.status = models.JobStatus.COMPLETED
        job.result = json.dumps(result)
        job.completed_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Job {job_id} completed successfully")
        return result
    
    except Exception as exc:
        logger.error(f"Job {job_id} failed: {str(exc)}")
        job.error = str(exc)
        
        # Retry with exponential backoff
        if job.attempts < job.max_attempts:
            backoff = 2 ** (job.attempts - 1)  # 1, 2, 4, 8, 16 seconds
            logger.info(f"Retrying job {job_id} in {backoff}s")
            job.status = models.JobStatus.PENDING
            db.commit()
            db.close()
            
            # Celery retries after backoff
            raise self.retry(exc=exc, countdown=backoff)
        else:
            # Max retries exceeded
            job.status = models.JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            db.commit()
            logger.error(f"Job {job_id} failed after {job.attempts} attempts")
    
    finally:
        db.close()


def handle_test_job(params: dict):
    """Example job executor"""
    import time
    duration = params.get("duration", 1)
    should_fail = params.get("should_fail", False)
    
    print(f"DEBUG: params={params}, should_fail={should_fail}, type={type(should_fail)}")
    
    time.sleep(duration)
    
    if should_fail:
        raise Exception("Intentional error for testing")
    
    return {"status": "completed", "duration": duration}