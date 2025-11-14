from app.celery_app import app
from app.database import SessionLocal
from app import models
from app.services.metrics import (
    notifications_sent, 
    notification_duration, 
    pending_notifications,
    push_metrics  # ← Import push function
)
import time
import json
from app.services.email_service import send_email
import asyncio
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.task(bind=True, max_retries=5)
def send_notification(self, notification_id: str):
    """Send notification across all channels"""
    
    db = SessionLocal()
    start_time = time.time()
    
    try:
        # Get notification from database
        notification = db.query(models.Notification).filter(
            models.Notification.id == notification_id
        ).first()
        user_id=notification.user_id
        user=db.query(models.User).filter(
            models.User.id==user_id
        ).first()
        email=user.email
        phone=user.phone
        message=notification.message
        title=notification.title
        channels=notification.channels

        
        if not notification:
            logger.error(f"Notification {notification_id} not found")
            return
        # Update gauge: increment pending
        pending_notifications.inc()
    
        
        logger.info(f"Sending notification {notification_id} via {channels}")
        
        # Send to each channel
        for channel in channels:
            channel_start = time.time()
            try:
                if channel == "email":
                    send_email_notification(notification,email,title,message)
                elif channel == "sms":
                    send_sms_notification(notification,phone,message,title)
                elif channel == "push":
                    send_push_notification(notification,message,title)
                elif channel == "in_app":
                 send_in_app_notification(notification,message,title)
                notifications_sent.labels(channel=channel, status="success").inc()
                notification_duration.labels(channel=channel).observe(time.time() - channel_start)
            except Exception as channel_error:
                notifications_sent.labels(channel=channel, status="failed").inc()
                logger.warning(f"Failed to send via {channel}: {str(channel_error)}")
                
        
        # Mark as sent
        # Push metrics after processing all channels
         
        notification.status = "sent"
        notification.sent_at = datetime.utcnow()
        db.commit()
        # Update gauge: decrement pending
        pending_notifications.dec()
        
        # Push ALL metrics to Pushgateway
        push_metrics()
        
        
        logger.info(f"Notification {notification_id} sent successfully")
        return {"status": "sent", "notification_id": notification_id}
    
    except Exception as exc:
        logger.error(f"Notification {notification_id} failed: {str(exc)}")
        notifications_sent.labels(channel="unknown", status="failed").inc()
        pending_notifications.dec()
        logger.info("[ERROR PATH] About to push metrics...")
        push_metrics()  # ← Push metrics even on failure
        logger.info(" [ERROR PATH] Returned from push_metrics()")
        
        if self.request.retries < self.max_retries:
            backoff = 2 ** self.request.retries
            logger.info(f"Retrying in {backoff}s")
            raise self.retry(exc=exc, countdown=backoff)
        else:
            notification.status = "failed"
            notifications_sent.labels(channel="unknown", status="failed").inc()
            db.commit()
            logger.error(f"Notification {notification_id} failed after retries")
    
    finally:
        db.close()


def send_email_notification(notification,email,title,message):
    """Send email notification""" 
    to_email = email
    subject = title
    body = f"{title}\n\n{message}"
    success = send_email(to_email, subject, body)
    if success:
        logger.info(f"[EMAIL] Sent to {to_email}")
    else:
        raise Exception(f"Failed to send email to {to_email}")

def send_sms_notification(notification,phone,message,title):
    """Send SMS notification"""
    from app.services.sms_service import send_sms
    to_number = phone # Test number format
    message = f"{title}\n{message}"
    success = send_sms(to_number, message)
    if success:
        logger.info(f"[SMS] Sent to {to_number}")
    else:
        raise Exception(f"Failed to send SMS to {to_number}")

def send_push_notification(notification,message,title):
    """Send push notification - placeholder"""
    logger.info(f"[PUSH] To user {notification.user_id}: {notification.title}")
    # TODO: Implement actual push sending

def send_in_app_notification(notification,message,title):
    """Send in-app notification via Redis Pub/Sub"""
    from app.services.redis_pubsub import redis_pubsub
    message = {
        "type": "notification",
        "title": title,
        "message": message,
        "notification_id": notification.notification_id
    }
    
    # Publish to user's channel
    redis_pubsub.publish_notification(notification.user_id, message)
    
    logger.info(f"[IN-APP] Published to user {notification.user_id}")