from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime

class JobCreate(BaseModel):
    job_type: str
    params: dict
    priority: int = Field(default=5, ge=1, le=10)

class JobResponse(BaseModel):
    job_id: str
    status: str
    job_type: str
    attempts: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    result: Optional[Any]
    error: Optional[str]
    
    class Config:
        from_attributes = True