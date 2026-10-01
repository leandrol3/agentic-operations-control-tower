"""Producer: commit do claim antes de publicar; reenvio explícito cobre a janela de publicação."""
from .idempotency import idempotency_key
from .store import Store
from .tasks import execute


def enqueue(envelope, options, operation='analyze-reference', version='v1', store=None):
    if options.llm_mode == 'openai':
        from .llm_runtime import settings_for
        settings_for(options)  # chave/modelo/configuração válidos antes de persistir/publicar
    store = store or Store()
    key = idempotency_key(envelope.incident_id, operation, version)
    execution, created = store.claim(envelope, key, options)
    # Repetir enqueue reenvia a mesma identidade. Mesmo terminal é seguro: worker não a reexecuta.
    execute.apply_async(kwargs={'envelope': envelope.model_dump(mode='json'),
        'execution_id': str(execution.execution_id), 'idempotency_key': key}, task_id=str(execution.execution_id))
    return execution, created
