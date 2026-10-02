"""Associação 1:1 aditiva. Não modifica documentos/contratos da Aula 2."""
from psycopg.types.json import Jsonb
from ..distributed.durable import TaskOptions
from ..distributed.store import Store
from ..telemetry.context import ExecutionContext, current_context

CONTEXT_SCHEMA = '''
CREATE TABLE IF NOT EXISTS ct_execution_context (
 execution_id uuid PRIMARY KEY REFERENCES ct_executions(execution_id),
 document jsonb NOT NULL
);
'''


class CorrelatedStore(Store):
    def initialize(self):
        super().initialize()
        with self.connect() as conn:
            conn.execute(CONTEXT_SCHEMA)

    def claim(self, envelope, key, options):
        execution, created = super().claim(envelope, key, options)
        context = current_context.get()
        if context is None:
            raise RuntimeError('Submission exige contexto explícito')
        proposed = context.model_copy(update={'execution_id': execution.execution_id,
                                               'incident_id': execution.incident_id})
        with self.connect() as conn, conn.transaction():
            conn.execute('INSERT INTO ct_execution_context VALUES (%s,%s) ON CONFLICT DO NOTHING',
                         (execution.execution_id, Jsonb(proposed.model_dump(mode='json'))))
            row = conn.execute('SELECT document FROM ct_execution_context WHERE execution_id=%s',
                               (execution.execution_id,)).fetchone()
        # Primeira associação vence: duplicatas/retries preservam a correlação original.
        current_context.set(ExecutionContext.model_validate(row['document']))
        return execution, created

    def context(self, execution_id):
        with self.connect() as conn:
            row = conn.execute('SELECT document FROM ct_execution_context WHERE execution_id=%s',
                               (execution_id,)).fetchone()
            return ExecutionContext.model_validate(row['document']) if row else None

    def options_for(self, execution_id):
        """Read persisted model selection; economics never guesses from current config."""
        with self.connect() as conn:
            row = conn.execute('SELECT options FROM ct_executions WHERE execution_id=%s',
                               (execution_id,)).fetchone()
            if not row:
                raise ValueError('Execution não encontrada')
            return TaskOptions.model_validate(row['options'])


    def list_incidents(self, *, status=None, limit=20):
        """Bounded public projection; values parameterized, deterministic tie-break."""
        if status not in (None, 'queued', 'running', 'completed', 'failed') or not 1 <= limit <= 100:
            raise ValueError('Filtro/limite inválido')
        with self.connect() as conn:
            return conn.execute("""
                SELECT document->>'incident_id' AS incident_id, execution_id,
                       document->>'status' AS status,
                       document->'result'->>'outcome' AS outcome,
                       document->'result'->'approval'->>'status' AS approval_status,
                       created_at, document->>'completed_at' AS completed_at
                FROM ct_executions
                WHERE (%s::text IS NULL OR document->>'status' = %s)
                ORDER BY created_at DESC, execution_id DESC
                LIMIT %s
            """, (status, status, limit)).fetchall()
