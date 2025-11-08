from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.workers.tasks import execute_job
import uuid
import json

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.post("/", response_model=schemas.JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_job(
    job: schemas.JobCreate,
    db: Session = Depends(get_db)
):
    """Create a new job and queue it"""
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Save to database
    db_job = models.Job(
        job_id=job_id,
        job_type=job.job_type,
        params=json.dumps(job.params),
        status=models.JobStatus.PENDING,
        max_attempts=5
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    
    # Queue the job (Celery will execute it)
    execute_job.delay(job_id)
    
    return db_job


@router.get("/{job_id}", response_model=schemas.JobResponse)
async def get_job(job_id: str, db: Session = Depends(get_db)):
    """Get job status"""
    
    job = db.query(models.Job).filter(models.Job.job_id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job


@router.get("/", response_model=list[schemas.JobResponse])
async def list_jobs(
    status: str = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List jobs with optional filtering"""
    
    query = db.query(models.Job)
    
    if status:
        query = query.filter(models.Job.status == status)
    
    return query.limit(limit).all()


@router.delete("/{job_id}")
async def cancel_job(job_id: str, db: Session = Depends(get_db)):
    """Cancel a pending job"""
    
    job = db.query(models.Job).filter(models.Job.job_id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status == models.JobStatus.PROCESSING:
        raise HTTPException(status_code=400, detail="Cannot cancel processing job")
    
    job.status = models.JobStatus.FAILED
    job.error = "Cancelled by user"
    db.commit()
    
    return {"message": "Job cancelled"}