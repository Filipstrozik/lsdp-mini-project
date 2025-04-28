from datetime import timedelta
from celery.schedules import crontab
# Broker settings
broker_url = "amqp://user:password@rabbitmq:5672//"
result_backend = "redis://redis:6379/0"

# Task serialization
task_serializer = "json"
accept_content = ["json"]
result_serializer = "json"

# Beat schedule settings
beat_schedule = {
    "scrape-polwro-full-daily": {
        "task": "scraper.tasks.run_polwro_scraper",
        "schedule": timedelta(days=1),  # Run every day
        "kwargs": {"full_scan": False},
    }
}

# Time zone
timezone = "Europe/Warsaw"
