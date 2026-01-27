"""Celery app for Scheduled SCRAM API tasks."""

from celery import Celery

from .settings import settings

scram_api_scheduler = Celery(
    "scram_api_scheduler",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

scram_api_scheduler.conf.update(
    result_expires=604800,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    include=["scheduler.tasks"],
    broker_connection_retry_on_startup=True,
    worker_send_task_events=True,
    task_send_sent_event=True,
    worker_prefetch_multiplier=1,
    worker_pool_restarts=True,
    beat_schedule={
        "perform-process-updates": {
            "task": "scheduler.tasks.perform_process_updates",
            "schedule": settings.process_updates_interval,
        },
    },
)

if settings.disable_process_updates:
    scram_api_scheduler.conf.beat_schedule.pop("perform-process-updates")
