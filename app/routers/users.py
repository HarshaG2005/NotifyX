from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from fastapi.security import OAuth2PasswordBearer
from app.oauth2 import get_current_user
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import User, Notification
from app.schemas import UserCreate, UserUpdate, UserResponse, NotificationResponse, TokenData
from app.utils import hash
import logging
from slowapi import Limiter
from slowapi.util import get_remote_address
router = APIRouter(prefix="/users", tags=["Users"])
logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)  # Rate limiter instance
#============ USER ROUTES =============

#***********CREATE USER ********************************************
@router.post("/", response_model=UserResponse, status_code=201)
@limiter.limit("5/minute")  # Rate limit: 5 requests per minute
def create_user(request: Request,user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user
    
    - **email**: User's email (required, unique)
    - **phone**: User's phone number (optional)
    - **full_name**: User's full name (optional)
    - **preferences**: Notification preferences (optional)
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    user_data = user.model_dump()
    
    user_data['password'] = hash(user_data['password'])  # Hash it
    
    # Convert Pydantic model to dict, handling preferences
    
    if user_data.get('preferences'):
        user_data['preferences'] = user_data['preferences'].model_dump() if hasattr(user_data['preferences'], 'model_dump') else user_data['preferences']
    
    db_user = User(**user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    logger.info(f"Created user {db_user.id} ({db_user.email})")
    return db_user
#***********LIST USERS ********************************************
@router.get("/", response_model=List[UserResponse],)
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    List all users with pagination
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 100)
    - **is_active**: Filter by active status (optional)
    """
    query = db.query(User)
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    users = query.offset(skip).limit(limit).all()
    return users
#***********GET USER ********************************************
@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db),current_user:TokenData= Depends(get_current_user)):
    """
    Get a specific user by ID
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

#***********UPDATE USER ********************************************

@router.put("/{user_id}", response_model=UserResponse)
@limiter.limit("5/minute")  # Rate limit: 5 requests per minute
def update_user(request: Request,user_id: int, user_update: UserUpdate, db: Session = Depends(get_db),current_user:TokenData= Depends(get_current_user)):
    """
    Update user information
    
    - **phone**: Update phone number
    - **full_name**: Update full name
    - **is_active**: Activate/deactivate user
    - **preferences**: Update notification preferences
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update only provided fields
    update_data = user_update.model_dump(exclude_unset=True)
    
    # Handle preferences separately if provided
    if 'preferences' in update_data and update_data['preferences']:
        update_data['preferences'] = update_data['preferences'].model_dump() if hasattr(update_data['preferences'], 'model_dump') else update_data['preferences']
    
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    
    logger.info(f"Updated user {user_id}")
    return db_user
#***********DELETE USER ********************************************
@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db),current_user:TokenData= Depends(get_current_user)):
    """
    Delete a user (soft delete by setting is_active=False)
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Soft delete
    db_user.is_active = False
    db.commit()
    
    logger.info(f"Deleted (deactivated) user {user_id}")
    return None
#***********GET USER NOTIFICATIONS ********************************************
@router.get("/{user_id}/notifications", response_model=List[NotificationResponse])
def get_user_notifications(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user:TokenData= Depends(get_current_user)
):
    """
    Get all notifications for a specific user
    """
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    notifications = db.query(Notification)\
        .filter(Notification.user_id == user_id)\
        .order_by(Notification.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return notifications

#***********GET USER PREFERENCES ********************************************
@router.get("/{user_id}/preferences", response_model=dict)
def get_user_preferences(user_id: int, db: Session = Depends(get_db),current_user:TokenData= Depends(get_current_user)):
    """
    Get user's notification preferences
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user.preferences
#***********UPDATE USER PREFERENCES ********************************************
@router.put("/{user_id}/preferences", response_model=dict)
@limiter.limit("5/minute")  # Rate limit: 5 requests per minute
def update_user_preferences(
    request: Request,
    user_id: int,
    preferences: dict,
    db: Session = Depends(get_db),
    current_user:TokenData= Depends(get_current_user)
):
    """
    Update user's notification preferences
    
    Example:
    ```json
    {
        "email": true,
        "sms": false,
        "push": true,
        "in_app": true
    }
    ```
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate preference keys
    valid_channels = {"email", "sms", "push", "in_app"}
    if not all(key in valid_channels for key in preferences.keys()):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid preference keys. Valid keys: {valid_channels}"
        )
    
    # Update preferences (merge with existing)
    current_prefs = user.preferences or {}
    current_prefs.update(preferences)
    user.preferences = current_prefs
    
    db.commit()
    db.refresh(user)
    
    logger.info(f"Updated preferences for user {user_id}")
    return user.preferences