from app.celery_app import app
from app.database import SessionLocal
from app import models
from app.services.metrics import notifications_sent, notification_duration
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
            models.Notification.notification_id == notification_id
        ).first()
        
        if not notification:
            logger.error(f"Notification {notification_id} not found")
            return
        
        # Parse channels
        channels = json.loads(notification.channels)
        
        logger.info(f"Sending notification {notification_id} via {channels}")
        
        # Send to each channel
        for channel in channels:
            try:
                if channel == "email":
                    send_email_notification(notification)
                elif channel == "sms":
                    send_sms_notification(notification)
                elif channel == "push":
                    send_push_notification(notification)
                elif channel == "in_app":
                 send_in_app_notification(notification)
                notifications_sent.labels(channel=channel, status="success").inc()
                notification_duration.labels(channel=channel).observe(time.time() - channel_start)
            except Exception as channel_error:
                logger.warning(f"Failed to send via {channel}: {str(channel_error)}")
                notifications_sent.labels(channel=channel, status="failed").inc()
        
        # Mark as sent
        notification.status = "sent"
        notification.sent_at = datetime.utcnow()
        db.commit()
        
        
        logger.info(f"Notification {notification_id} sent successfully")
        return {"status": "sent", "notification_id": notification_id}
    
    except Exception as exc:
        logger.error(f"Notification {notification_id} failed: {str(exc)}")
        
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


def send_email_notification(notification):
    """Send email notification"""
    
    
    # For now, use notification.user_id as email
    # Later you'd look up user's actual email from database
    to_email = f"user{notification.user_id}@example.com"
    
    subject = notification.title
    body = f"{notification.title}\n\n{notification.message}"
    
    success = send_email(to_email, subject, body)
    
    if success:
        logger.info(f"[EMAIL] Sent to {to_email}")
    else:
        raise Exception(f"Failed to send email to {to_email}")

def send_sms_notification(notification):
    """Send SMS notification"""
    from app.services.sms_service import send_sms
    
    # For now, use placeholder number
    to_number = f"+1208826549{notification.user_id}"  # Test number format
    
    message = f"{notification.title}\n{notification.message}"
    
    success = send_sms(to_number, message)
    
    if success:
        logger.info(f"[SMS] Sent to {to_number}")
    else:
        raise Exception(f"Failed to send SMS to {to_number}")

def send_push_notification(notification):
    """Send push notification - placeholder"""
    logger.info(f"[PUSH] To user {notification.user_id}: {notification.title}")
    # TODO: Implement actual push sending

def send_in_app_notification(notification):
    """Send in-app notification via Redis Pub/Sub"""
    from app.services.redis_pubsub import redis_pubsub
    
    message = {
        "type": "notification",
        "title": notification.title,
        "message": notification.message,
        "notification_id": notification.notification_id
    }
    
    # Publish to user's channel
    redis_pubsub.publish_notification(notification.user_id, message)
    
    logger.info(f"[IN-APP] Published to user {notification.user_id}")