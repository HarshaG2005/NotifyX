from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum,ForeignKey,Boolean,JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()


class NotificationStatus(str,enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
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