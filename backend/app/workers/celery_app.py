from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()
celery_app = Celery(
    "applysense",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.pipeline"],
)


def _parse_cron(expr: str):
    minute, hour, day_of_month, month_of_year, day_of_week = expr.split()
    return crontab(
        minute=minute,
        hour=hour,
        day_of_month=day_of_month,
        month_of_year=month_of_year,
        day_of_week=day_of_week,
    )


celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "daily-job-ingestion": {
            "task": "app.tasks.pipeline.job_ingestion",
            "schedule": _parse_cron(settings.job_ingest_cron),
        },
        "poll-gmail-updates": {
            "task": "app.tasks.pipeline.email_monitoring",
            "schedule": _parse_cron(settings.email_monitor_cron),
        },
    },
)
