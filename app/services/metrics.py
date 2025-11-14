from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, push_to_gateway
import os
import logging

# Configure logging properly
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Separate registry for worker metrics
worker_registry = CollectorRegistry()

# ALL metrics must use worker_registry
notifications_sent = Counter(
    'notifications_sent_total',
    'Total notifications sent',
    ['channel', 'status'],
    registry=worker_registry
)

notification_duration = Histogram(
    'notification_duration_seconds',
    'Time taken to send notification',
    ['channel'],
    registry=worker_registry
)

pending_notifications = Gauge(
    'pending_notifications',
    'Number of pending notifications',
    registry=worker_registry
)

def push_metrics():
    """Push all metrics (counters, histograms, gauges) to Pushgateway"""
    pushgateway_url = os.getenv("PUSHGATEWAY_URL", "localhost:9091")
    
    # Remove http:// or https:// if present
    pushgateway_url = pushgateway_url.replace("http://", "").replace("https://", "")
    
    logger.info("=" * 60)
    logger.info("PUSH METRICS CALLED")
    logger.info(f" Target: {pushgateway_url}")
    logger.info(f" Registry has {len(list(worker_registry.collect()))} metric families")
    
    # Log current metric values
    for metric_family in worker_registry.collect():
        logger.info(f"   Metric: {metric_family.name}")
        for sample in metric_family.samples:
            logger.info(f"      {sample.name}{sample.labels} = {sample.value}")
    
    try:
        logger.info("⏳ Pushing to Pushgateway...")
        push_to_gateway(
            pushgateway_url, 
            job='celery_workers',
            registry=worker_registry
        )
        logger.info(" Metrics pushed to Pushgateway successfully!")
        logger.info("=" * 60)
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f" FAILED to push metrics!")
        logger.error(f" Error type: {type(e).__name__}")
        logger.error(f" Error message: {str(e)}")
        logger.error("=" * 60)
        import traceback
        logger.error(traceback.format_exc())