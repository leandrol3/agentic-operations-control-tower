"""Postgres: claim único, eventos transacionais e lock de sessão por execução.

Não há transação aberta durante o workflow. O advisory lock vive na sessão;
a morte do processo libera a sessão. Não é lease nem exactly-once.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
from threading import RLock
from uuid import uuid4
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from .config import database_url, MAX_ATTEMPTS
from .durable import DurableExecution, DurableEvent, TaskOptions

SCHEMA = '''
CREATE TABLE IF NOT EXISTS ct_executions (
 execution_id uuid PRIMARY KEY,
 idempotency_key text NOT NULL UNIQUE,
 document jsonb NOT NULL,
 envelope jsonb NOT NULL,
 options jsonb NOT NULL,
 attempts integer NOT NULL DEFAULT 0,
 event_sequence integer NOT NULL DEFAULT 0,
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS ct_events (
 execution_id uuid NOT NULL REFERENCES ct_executions,
 sequence integer NOT NULL,
 document jsonb NOT NULL,
 PRIMARY KEY(execution_id, sequence)
);
'''


class Store:
    def __init__(self, dsn=None):
        self.dsn = dsn or database_url()

    def connect(self):
        return psycopg.connect(self.dsn, autocommit=True, row_factory=dict_row, connect_timeout=5)

    def initialize(self):
        with self.connect() as conn, conn.transaction():
            conn.execute(SCHEMA)

    def claim(self, envelope, key, options):
        execution = DurableExecution(execution_id=uuid4(), incident_id=envelope.incident_id, idempotency_key=key, llm_mode=options.llm_mode)
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
            if existing['envelope'] != envelope.model_dump(mode='json') or TaskOptions.model_validate(existing['options']) != options:
                raise ValueError('Mesma chave com payload/opções diferentes; use outra version')
            return DurableExecution.model_validate(existing['document']), False

    def get(self, execution_id):
        with self.connect() as conn:
            row = conn.execute('SELECT document FROM ct_executions WHERE execution_id=%s', (execution_id,)).fetchone()
            if not row:
                raise ValueError('Execution não encontrada')
            return DurableExecution.model_validate(row['document'])

    def list(self, limit=8):
        with self.connect() as conn:
            counts = conn.execute("SELECT document->>'status' AS status,count(*) AS count FROM ct_executions GROUP BY 1").fetchall()
            recent = conn.execute('SELECT document FROM ct_executions ORDER BY created_at DESC LIMIT %s', (limit,)).fetchall()
            return {r['status']: r['count'] for r in counts}, [DurableExecution.model_validate(r['document']) for r in recent]

    def events(self, execution_id):
        self.get(execution_id)
        with self.connect() as conn:
            return [DurableEvent.model_validate(r['document']) for r in conn.execute(
                'SELECT document FROM ct_events WHERE execution_id=%s ORDER BY sequence', (execution_id,))]

    @contextmanager
    def acquire(self, execution_id, key, envelope):
        with self.connect() as conn:
            locked = conn.execute('SELECT pg_try_advisory_lock(hashtextextended(%s,0)) AS ok', (key,)).fetchone()['ok']
            if not locked:
                yield None
                return
            # Connection closure releases lock, even after exceptions.
            row = conn.execute('SELECT * FROM ct_executions WHERE execution_id=%s AND idempotency_key=%s', (execution_id, key)).fetchone()
            if not row or row['envelope'] != envelope:
                raise ValueError('Mensagem não corresponde ao claim persistido')
            yield Session(conn, DurableExecution.model_validate(row['document']), row['attempts'], row['options'])


class Session:
    def __init__(self, conn, execution, attempts=0, options=None):
        self.conn, self.execution = conn, execution
        self.attempts, self.options = attempts, options
        self.lock = RLock()  # callbacks LangGraph paralelos compartilham uma conexão

    def event(self, kind, agent='worker', detail=None, duration_ms=None, input_tokens=None, output_tokens=None):
        with self.lock, self.conn.transaction():
            seq = self.conn.execute('UPDATE ct_executions SET event_sequence=event_sequence+1 WHERE execution_id=%s RETURNING event_sequence',
                                    (self.execution.execution_id,)).fetchone()['event_sequence']
            event = DurableEvent(execution_id=self.execution.execution_id, incident_id=self.execution.incident_id,
                agent_id=agent, event_type=kind, timestamp=datetime.now(timezone.utc), status=self.execution.status,
                sequence=seq, attempt=self.execution.attempt, detail=detail, duration_ms=duration_ms,
                input_tokens=input_tokens, output_tokens=output_tokens)
            self.conn.execute('INSERT INTO ct_events VALUES (%s,%s,%s)',
                              (event.execution_id, seq, Jsonb(event.model_dump(mode='json'))))

    def update(self, **fields):
        self.execution = DurableExecution.model_validate(self.execution.model_dump() | fields)
        self.conn.execute('UPDATE ct_executions SET document=%s, attempts=%s WHERE execution_id=%s',
                          (Jsonb(self.execution.model_dump(mode='json')), self.attempts, self.execution.execution_id))

    def begin(self, worker):
        with self.lock, self.conn.transaction():
            if self.execution.status in ('completed', 'failed'):
                return False
            if self.execution.status == 'running':
                self.event('execution.interrupted', detail='Reentrega adquiriu lock liberado; tentativa anterior sem término')
            if self.attempts >= MAX_ATTEMPTS:
                self.update(status='failed', completed_at=datetime.now(timezone.utc), current_step='failed', error='Limite de tentativas atingido')
                self.event('execution.failed', detail='Limite durável; evita ciclo de redelivery')
                return False
            self.attempts += 1
            self.update(status='running', attempt=self.attempts, worker_id=worker, started_at=datetime.now(timezone.utc),
                        completed_at=None, current_step='workflow', error=None)
            self.event('execution.started')
            return True

    def step(self, agent, phase, duration=None):
        with self.lock, self.conn.transaction():
            self.update(current_step=agent)
            self.event(agent + '.' + {'início': 'started', 'fim': 'completed', 'erro': 'failed'}[phase], agent, duration_ms=duration)

    def finish(self, result, duration_ms=None):
        with self.lock, self.conn.transaction():
            self.update(status='completed', completed_at=datetime.now(timezone.utc), current_step=result.outcome if result.outcome != 'recommendation' else 'awaiting_approval',
                        workflow_status=None if result.outcome == 'human_review_required' else 'awaiting_approval',
                        result=result, duration_ms=duration_ms)
            self.event('execution.completed')

    def fail(self, message, retry):
        with self.lock, self.conn.transaction():
            self.update(status='failed', completed_at=datetime.now(timezone.utc), current_step='failed', error=message)
            self.event('execution.failed', detail=message)
            if retry:
                self.update(status='queued', started_at=None, completed_at=None, worker_id=None, current_step=None, error=None)
                self.event('execution.retry', detail='Nova tentativa completa; backoff 2/4 segundos')
