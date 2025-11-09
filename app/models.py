from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum,ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class JobStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True)
    job_id = Column(String, unique=True, index=True)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING)
    job_type = Column(String)
    params = Column(Text)
    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    worker_id = Column(String, nullable=True)

class NotificationChannel(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True)
    notification_id = Column(String, unique=True, index=True)
    user_id = Column(Integer)#ForeignKey('users.id', ondelete='CASCADE')
    title = Column(String)
    message = Column(String)
    channels = Column(Text)  # JSON string
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)