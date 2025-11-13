from app.models import User  # Add import

@celery.task(bind=True, max_retries=3)
def send_notification(self, notification_id, user_id, title, message, channels):
    """Send notification through multiple channels"""
    
    logger.info(f"Sending notification {notification_id} via {channels}")
    
    start_time = time.time()
    
    # ✅ Get user info from database
    from app.database import SessionLocal
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            logger.error(f"User {user_id} not found")
            raise Exception(f"User {user_id} not found")
        
        # ✅ Use actual user data
        user_email = user.email
        user_phone = user.phone
        
        # Send through each channel
        for channel in channels:
            try:
                if channel == "email" and user_email:
                    email_service.send_email(user_email, title, message)
                    logger.info(f"[EMAIL] Sent to {user_email}")
                    notifications_sent.labels(channel="email", status="success").inc()
                
                elif channel == "sms" and user_phone:
                    sms_service.send_sms(user_phone, message)
                    logger.info(f"[SMS] Sent to {user_phone}")
                    notifications_sent.labels(channel="sms", status="success").inc()
                
                elif channel == "push":
                    push_service.send_push(user_id, title, message)
                    logger.info(f"[PUSH] Sent to user {user_id}")
                    notifications_sent.labels(channel="push", status="success").inc()
                
                elif channel == "in_app":
                    redis_client.publish(
                        f"notifications:user:{user_id}",
                        json.dumps({"title": title, "message": message, "timestamp": str(time.time())})
                    )
                    logger.info(f"[IN-APP] Published to user {user_id}")
                    notifications_sent.labels(channel="in_app", status="success").inc()
                
                # Track duration per channel
                notification_duration.labels(channel=channel).observe(time.time() - start_time)
            
            except Exception as channel_exc:
                logger.error(f"Failed to send via {channel}: {str(channel_exc)}")
                notifications_sent.labels(channel=channel, status="failed").inc()
        
        # Update notification status in DB
        from app.models import Notification, NotificationStatus
        db_notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if db_notification:
            db_notification.status = NotificationStatus.SENT
            db_notification.sent_at = func.now()
            db.commit()
        
        logger.info(f"Notification {notification_id} sent successfully")
        
        pending_notifications.dec()
        push_metrics()
        
        return {"status": "sent", "notification_id": notification_id}
    
    except Exception as exc:
        logger.error(f"Notification {notification_id} failed: {str(exc)}")
        notifications_sent.labels(channel="unknown", status="failed").inc()
        pending_notifications.dec()
        push_metrics()
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)
        else:
            # Update to failed status
            db_notification = db.query(Notification).filter(Notification.id == notification_id).first()
            if db_notification:
                db_notification.status = NotificationStatus.FAILED
                db.commit()
            raise
    
    finally:
        db.close()