from app.celery_app import app
from app.database import SessionLocal
from app import models
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.task(bind=True, max_retries=5)
def send_notification(self, notification_id: str):
    """Send notification across all channels"""
    
    db = SessionLocal()
    
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
            except Exception as channel_error:
                logger.warning(f"Failed to send via {channel}: {str(channel_error)}")
        
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
            db.commit()
            logger.error(f"Notification {notification_id} failed after retries")
    
    finally:
        db.close()


def send_email_notification(notification):
    """Send email notification"""
    from app.services.email_service import send_email
    
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
    """Send SMS - placeholder"""
    logger.info(f"[SMS] To user {notification.user_id}: {notification.message}")
    # TODO: Implement actual SMS sending


def send_push_notification(notification):
    """Send push notification - placeholder"""
    logger.info(f"[PUSH] To user {notification.user_id}: {notification.title}")
    # TODO: Implement actual push sending


def send_in_app_notification(notification):
    """Send in-app notification - placeholder"""
    logger.info(f"[IN-APP] To user {notification.user_id}: {notification.title}")
    # TODO: Implement actual in-app sending