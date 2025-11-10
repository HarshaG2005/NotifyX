from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.workers.notification_tasks import send_notification
from fastapi import WebSocket
from typing import Set
import asyncio


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
# @router.websocket("/ws")
# async def websocket_broadcast(websocket: WebSocket):
#     await websocket.accept()
#     await websocket.send_text("✅ Connection established!")

#     try:
#         while True:
#             data = await websocket.receive_text()
#             await websocket.send_text(f"Echo: {data}")
#     except Exception as e:
#         print(f"WebSocket closed: {e}")

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

#Store connected clients
# connected_clients: Set[WebSocket] = set()

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