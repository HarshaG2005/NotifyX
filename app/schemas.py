from pydantic import BaseModel, EmailStr, Field,field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


# ============= USER SCHEMAS =============

class UserPreferences(BaseModel):
    email: bool = True
    sms: bool = True
    push: bool = True
    in_app: bool = True

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    phone: Optional[str] = None
    full_name: Optional[str] = None
    preferences: Optional[UserPreferences] = None
    @field_validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "phone": "+1234567890",
                "full_name": "John Doe",
                "preferences": {
                    "email": True,
                    "sms": False,
                    "push": True,
                    "in_app": True
                }
            }
        }

class UserUpdate(BaseModel):
    phone: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    preferences: Optional[UserPreferences] = None

class UserResponse(BaseModel):
    id: int
    email: str
    phone: Optional[str]
    full_name: Optional[str]
    is_active: bool
    preferences: Dict[str, bool]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# ============= NOTIFICATION SCHEMAS =============

class NotificationCreate(BaseModel):
    user_id: int
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1)
    channels: List[str] = Field(..., min_items=1)
   # metadata: Optional[Dict[str, Any]] = {}
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "title": "Welcome!",
                "message": "Welcome to our platform",
                "channels": ["email", "in_app"],
                "metadata": {"campaign": "onboarding"}
            }
        }

class NotificationResponse(BaseModel):
    id: str
    user_id: int
    title: str
    message: str
    channels: List[str]
    status: NotificationStatus
    #metadata: Dict[str, Any]
    created_at: datetime
    sent_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# ============= LOGIN SCHEMAS =============


class UserLogin(BaseModel):
    email:EmailStr
    password:str
class Token(BaseModel):
    access_token:str
    token_type:str
class TokenData(BaseModel):
    id:Optional[int]=None