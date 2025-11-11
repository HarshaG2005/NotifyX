from prometheus_client import Counter, Histogram, Gauge
import time

# Counters (total count)
notifications_sent = Counter(
    'notifications_sent_total',
    'Total notifications sent',
    ['channel', 'status']
)

jobs_processed = Counter(
    'jobs_processed_total',
    'Total jobs processed',
    ['job_type', 'status']
)

# Histograms (track time)
notification_duration = Histogram(
    'notification_duration_seconds',
    'Time taken to send notification',
    ['channel']
)

job_duration = Histogram(
    'job_duration_seconds',
    'Time taken to process job',
    ['job_type']
)

# Gauges (current value)
active_jobs = Gauge(
    'active_jobs',
    'Number of active jobs'
)

pending_notifications = Gauge(
    'pending_notifications',
    'Number of pending notifications'
)