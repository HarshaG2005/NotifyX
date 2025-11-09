from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.workers.notification_tasks import send_notification
import uuid
import json

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.post("/", response_model=schemas.NotificationResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_notification(
    notification: schemas.NotificationCreate,
    db: Session = Depends(get_db)
):
    """Create and queue notification"""
    
    notification_id = str(uuid.uuid4())
    
    db_notification = models.Notification(
        notification_id=notification_id,
        user_id=notification.user_id,
        title=notification.title,
        message=notification.message,
        channels=json.dumps(notification.channels),
        status="pending"
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    
    # Convert channels back to list for response
    db_notification.channels = json.loads(db_notification.channels)  # Deserialize for response
    
    # Queue the notification job
    send_notification.delay(notification_id)
    return db_notification
@router.get("/user/{user_id}")
async def get_user_notifications(user_id: int, db: Session = Depends(get_db)):
    """Get all notifications for a user"""
    
    notifications = db.query(models.Notification).filter(
        models.Notification.user_id == user_id
    ).all()
    
    return notifications

@router.get("/{notification_id}", response_model=schemas.NotificationResponse)
async def get_notification(notification_id: str, db: Session = Depends(get_db)):
    """Get notification status"""
    
    notification = db.query(models.Notification).filter(
        models.Notification.notification_id == notification_id
    ).first()
    notification.channels = json.loads(notification.channels)  # Deserialize for response
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return notification


