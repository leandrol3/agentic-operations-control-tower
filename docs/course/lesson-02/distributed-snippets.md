# Trechos prontos para projeção — Aula 2

Não digitar ao vivo. Abrir somente o trecho que esclarece a decisão; versões completas são a fonte de verdade.

## Celery task: fronteira de execução

Origem: `tasks.py`.

```python
@app.task(bind=True, name='control_tower.execute', max_retries=2)
def execute(self, envelope, execution_id, idempotency_key):
    envelope = IncidentEnvelope.model_validate(envelope).model_dump(mode='json')
    store = Store()
    with store.acquire(execution_id, idempotency_key, envelope) as session:
        if session is None:  # outra entrega já está processando, não cria execução
            return {'execution_id': execution_id, 'duplicate': True}
        if not session.begin(f'{self.request.hostname}:{os.getpid()}'):
            return {'execution_id': execution_id, 'status': session.execution.status}
        options = TaskOptions.model_validate(session.options)
```

## Claim atômico: identidade única

Origem: `store.py`.

```python
    def claim(self, envelope, key, options):
        execution = DurableExecution(execution_id=uuid4(), incident_id=envelope.incident_id, idempotency_key=key)
        with self.connect() as conn, conn.transaction():
            row = conn.execute('''INSERT INTO ct_executions
                (execution_id,idempotency_key,document,envelope,options)
                VALUES (%s,%s,%s,%s,%s) ON CONFLICT (idempotency_key) DO NOTHING RETURNING execution_id''',
                (execution.execution_id, key, Jsonb(execution.model_dump(mode='json')),
                 Jsonb(envelope.model_dump(mode='json')), Jsonb(options.model_dump(mode='json')))).fetchone()
            if row:
                Session(conn, execution).event('execution.queued', 'producer')
                return execution, True
            existing = conn.execute('SELECT document,envelope,options FROM ct_executions WHERE idempotency_key=%s', (key,)).fetchone()
            if existing['envelope'] != envelope.model_dump(mode='json') or existing['options'] != options.model_dump(mode='json'):
                raise ValueError('Mesma chave com payload/opções diferentes; use outra version')
            return DurableExecution.model_validate(existing['document']), False
```

## Execution: contrato base + extensão durável

Origem: `models.py / durable.py`.

```python
class Execution(Contract):
    execution_id: UUID
    incident_id: Text
    status: Status = 'queued'
    started_at: AwareDatetime | None = None
    completed_at: AwareDatetime | None = None
    current_step: Text | None = None
    attempt: Annotated[int, Field(ge=1)] = 1
    worker_id: Text | None = None
    error: Text | None = None
    workflow_status: Literal['awaiting_approval', 'blocked'] | None = None

class DurableExecution(Execution):
    idempotency_key: Text
    result: FinalResult | None = None

    @model_validator(mode='after')
    def result_matches_status(self):
        if (self.status == 'completed') != (self.result is not None):
            raise ValueError('Somente completed exige resultado final')
        return self
```

## ExecutionEvent: campos preservados

Origem: `events.py`.

```python
class ExecutionEvent(Contract):
    execution_id: UUID
    incident_id: Text
    agent_id: Text
    event_type: EventType
    timestamp: AwareDatetime
    status: Status
    duration_ms: Milliseconds | None = None
    sequence: Annotated[int, Field(ge=1)]
    attempt: Annotated[int, Field(ge=1)] = 1
    input_tokens: Annotated[int, Field(ge=0)] | None = None
    output_tokens: Annotated[int, Field(ge=0)] | None = None
    estimated_cost: Money | None = None
    quality_score: Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)] | None = None
    business_outcome: Text | None = None
```

## Retry/ack/prefetch: configuração explícita

Origem: `celery_app.py`.

```python
"""Celery controla entregas; LangGraph continua controlando agentes."""
from celery import Celery
from .config import broker_url, QUEUE, VISIBILITY_TIMEOUT

app = Celery('control_tower', broker=broker_url(), include=['control_tower.distributed.tasks'])
app.conf.update(
    task_default_queue=QUEUE, task_serializer='json', accept_content=['json'],
    task_ignore_result=True, timezone='UTC', enable_utc=True,
    task_acks_late=True, task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    worker_cancel_long_running_tasks_on_connection_loss=True,
    broker_transport_options={'visibility_timeout': VISIBILITY_TIMEOUT},
    visibility_timeout=VISIBILITY_TIMEOUT,
    task_publish_retry=False, broker_connection_retry_on_startup=True,
)
```

## Persistência: resultado e evento na mesma transação

Origem: `store.py`.

```python
    def finish(self, result):
        with self.lock, self.conn.transaction():
            self.update(status='completed', completed_at=datetime.now(timezone.utc), current_step='awaiting_approval',
                        workflow_status='awaiting_approval', result=result)
            self.event('execution.completed')

    def event(self, kind, agent='worker', detail=None, duration_ms=None):
        with self.lock, self.conn.transaction():
            seq = self.conn.execute('UPDATE ct_executions SET event_sequence=event_sequence+1 WHERE execution_id=%s RETURNING event_sequence',
                                    (self.execution.execution_id,)).fetchone()['event_sequence']
            event = DurableEvent(execution_id=self.execution.execution_id, incident_id=self.execution.incident_id,
                agent_id=agent, event_type=kind, timestamp=datetime.now(timezone.utc), status=self.execution.status,
                sequence=seq, attempt=self.execution.attempt, detail=detail, duration_ms=duration_ms)
            self.conn.execute('INSERT INTO ct_events VALUES (%s,%s,%s)',
                              (event.execution_id, seq, Jsonb(event.model_dump(mode='json'))))
```

## Backoff e orçamento

Falha didática: `self.retry(countdown=2 ** session.attempts)`, máximo 3 tentativas duráveis.
A primeira falha aguarda 2 s; a segunda 4 s. Perda de processo inteiro usa redelivery, não self.retry.
Advisory lock de sessão vive até a conexão fechar; UNIQUE sozinho não impede duas tentativas simultâneas.
