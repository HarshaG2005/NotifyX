from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum,ForeignKey,Boolean,JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
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
class NotificationStatus(str,enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)  # For SMS notifications
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Notification preferences
    preferences = Column(JSON, default={
        "email": True,
        "sms": True,
        "push": True,
        "in_app": True
    })
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    notifications = relationship("Notification", back_populates="user")

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # Fixed!
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    channels = Column(JSON, nullable=False)  # ["email", "sms", "push", "in_app"]
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING)
   # metadata = Column(JSON, default={})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="notifications")