import redis
import json
import logging

logger = logging.getLogger(__name__)

class RedisPubSub:
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis = redis.from_url(redis_url, decode_responses=True)
    
    def publish_notification(self, user_id: int, notification: dict):
        """Publish notification to user's channel"""
        channel = f"notifications:user:{user_id}"
        message = json.dumps(notification)
        
        result = self.redis.publish(channel, message)
        logger.info(f"Published to {channel}: {result} subscribers")
        
        return result
    
    def subscribe(self, user_id: int):
        """Subscribe to user's notification channel"""
        channel = f"notifications:user:{user_id}"
        pubsub = self.redis.pubsub()
        pubsub.subscribe(channel)
        
        logger.info(f"Subscribed to {channel}")
        return pubsub

# Global instance
redis_pubsub = RedisPubSub()