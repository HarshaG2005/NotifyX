from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.workers.notification_tasks import send_notification
from fastapi import WebSocket
import asyncio
import uuid
import json
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.post("/", response_model=schemas.NotificationResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_notification(
    notification: schemas.NotificationCreate,
    db: Session = Depends(get_db)
):
    """Create and queue notification"""
    # ✅ Validate user exists
    user = db.query(models.User).filter(models.User.id == notification.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # ✅ Check if user is active
    if not user.is_active:
        raise HTTPException(status_code=400, detail="User is inactive")
    
    # ✅ Respect user preferences (filter channels)
    user_prefs = user.preferences or {}
    allowed_channels = [
        channel for channel in notification.channels 
        if user_prefs.get(channel, True)  # Default to True if not set
    ]
    
    if not allowed_channels:
        raise HTTPException(
            status_code=400,
            detail="All requested channels are disabled in user preferences"
        )
    
    notification_id = str(uuid.uuid4())
    
    db_notification = models.Notification(
        id=notification_id,
        user_id=notification.user_id,
        title=notification.title,
        message=notification.message,
        channels=allowed_channels,
        status="pending",
       # metadata=notification.metadata
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    
    send_notification.delay(
        notification_id,
        notification.user_id,
        notification.title,
        notification.message,
        allowed_channels  # ← Use filtered channels
    )
    logger.info(f"Queued notification {notification_id} for user {notification.user_id}")
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


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await websocket.accept()
    
    from app.services.redis_pubsub import redis_pubsub
    
    # Subscribe to Redis channel
    pubsub = redis_pubsub.subscribe(user_id)
    
    try:
        while True:
            # Listen for messages from Redis
            message = pubsub.get_message()
            
            if message and message["type"] == "message":
                data = json.loads(message["data"])
                await websocket.send_json(data)
            
            # Small delay to prevent CPU spinning
            await asyncio.sleep(0.1)
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        pubsub.close()