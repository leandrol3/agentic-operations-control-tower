"""Hooks Celery somente no runtime Aula 3. Nenhuma mudança na task/grafo."""
import logging
import os
from celery import signals
from ..telemetry.context import ExecutionContext, current_context
from ..telemetry.logging import log_event
from .store import CorrelatedStore

TASK = 'control_tower.execute'
HEADER = 'control_tower_context'


def before_publish(sender=None, headers=None, body=None, **kwargs):
    if sender != TASK or headers is None:
        return
    context = current_context.get()
    if context and str(context.execution_id) == body[1].get('execution_id'):
        headers[HEADER] = context.model_dump(mode='json')
    # Celery retry já preserva headers; não sobrescrever por contexto de outra execução.


def task_started(sender=None, task=None, kwargs=None, **unused):
    if getattr(sender, 'name', None) != TASK:
        return
    current_context.set(None)
    payload = (task.request.headers or {}).get(HEADER)
    try:
        context = ExecutionContext.model_validate(payload) if payload else None
        if context and str(context.execution_id) != kwargs['execution_id']:
            context = None
        # Recupera associação inclusive quando reenvio foi feito pela CLI histórica.
        if context is None:
            context = CorrelatedStore().context(kwargs['execution_id'])
        if context:
            current_context.set(context.model_copy(update={
                'worker_id': f'{task.request.hostname}:{os.getpid()}'}))
        log_event('worker.received', 'Entrega recebida; domínio decide claim e execução')
    except Exception:
        # Telemetria não impede o processamento; falha explícita sem expor DSN/exception.
        log_event('telemetry.context_unavailable', 'Contexto indisponível', level=logging.WARNING)


def task_finished(sender=None, task_id=None, kwargs=None, state=None, **unused):
    if getattr(sender, 'name', None) != TASK:
        return
    try:
        store = CorrelatedStore()
        execution = store.get(kwargs['execution_id'])
        # Snapshot pós-tentativa, não stream de eventos nem exactly-once de logs.
        for event in store.events(execution.execution_id):
            if event.attempt == execution.attempt and (
                    event.event_type.startswith('llm.') or event.event_type.endswith('.failed')
                    or event.event_type == 'execution.retry'):
                log_event(event.event_type, 'Evento durável observado após tentativa',
                          sequence=event.sequence, attempt=event.attempt,
                          level=logging.WARNING if event.event_type.endswith('.failed') else logging.INFO)
        log_event('worker.finished', 'Snapshot da execução persistida', status=execution.status,
                  attempt=execution.attempt, duration_ms=execution.duration_ms,
                  outcome=execution.result.outcome if execution.result else None)
    except Exception:
        log_event('telemetry.snapshot_unavailable', 'Consulte o histórico durável após recuperar o banco',
                  level=logging.WARNING)
    finally:
        current_context.set(None)


def install_signals():
    signals.before_task_publish.connect(before_publish, weak=False, dispatch_uid='lesson03.publish')
    signals.task_prerun.connect(task_started, weak=False, dispatch_uid='lesson03.start')
    signals.task_postrun.connect(task_finished, weak=False, dispatch_uid='lesson03.finish')
