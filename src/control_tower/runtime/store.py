"""Associação 1:1 aditiva. Não modifica documentos/contratos da Aula 2."""
from psycopg.types.json import Jsonb
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
