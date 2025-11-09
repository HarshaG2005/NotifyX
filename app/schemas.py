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
class NotificationCreate(BaseModel):
    user_id: int
    title: str
    message: str
    channels: list[str]

class NotificationResponse(BaseModel):
    notification_id: str
    user_id: int
    title: str
    message: str
    channels: list[str]
    status: str
    created_at: datetime
    sent_at: Optional[datetime]
    
    class Config:
        from_attributes = True