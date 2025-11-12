from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, push_to_gateway
import os
import logging

logger = logging.getLogger(__name__)

# Separate registry for worker metrics
worker_registry = CollectorRegistry()

# ALL metrics must use worker_registry
notifications_sent = Counter(
    'notifications_sent_total',
    'Total notifications sent',
    ['channel', 'status'],
    registry=worker_registry  # ← IMPORTANT
)

# jobs_processed = Counter(
#     'jobs_processed_total',
#     'Total jobs processed',
#     ['job_type', 'status'],
#     registry=worker_registry  # ← IMPORTANT
# )

notification_duration = Histogram(
    'notification_duration_seconds',
    'Time taken to send notification',
    ['channel'],
    registry=worker_registry  # ← IMPORTANT
)

# job_duration = Histogram(
#     'job_duration_seconds',
#     'Time taken to process job',
#     ['job_type'],
#     registry=worker_registry  # ← IMPORTANT


# Note: Gauges are trickier with push gateway (they snapshot current value)
# active_jobs = Gauge(
#     'active_jobs',
#     'Number of active jobs',
#     registry=worker_registry  # ← IMPORTANT
# )

pending_notifications = Gauge(
    'pending_notifications',
    'Number of pending notifications',
    registry=worker_registry  # ← IMPORTANT
)

def push_metrics():
    """Push all metrics (counters, histograms, gauges) to Pushgateway"""
    pushgateway_url = os.getenv("PUSHGATEWAY_URL", "localhost:9091")
    try:
        push_to_gateway(
            pushgateway_url, 
            job='celery_workers',
            registry=worker_registry  # This pushes ALL metrics in the registry
        )
        logger.debug("Metrics pushed to Pushgateway")
    except Exception as e:
        logger.error(f"Failed to push metrics: {e}")