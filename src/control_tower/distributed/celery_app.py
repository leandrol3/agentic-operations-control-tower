"""Celery controla entregas; LangGraph continua controlando agentes."""
from celery import Celery
from .config import broker_url, QUEUE, visibility_timeout

app = Celery('control_tower', broker=broker_url(), include=['control_tower.distributed.tasks'])
app.conf.update(
    task_default_queue=QUEUE, task_serializer='json', accept_content=['json'],
    task_ignore_result=True, timezone='UTC', enable_utc=True,
    task_acks_late=True, task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    worker_cancel_long_running_tasks_on_connection_loss=True,
    broker_transport_options={'visibility_timeout': visibility_timeout()},
    visibility_timeout=visibility_timeout(),
    task_publish_retry=False, broker_connection_retry_on_startup=True,
)
