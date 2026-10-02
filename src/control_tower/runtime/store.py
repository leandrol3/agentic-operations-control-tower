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

    def control_plane_samples(self, *, limit=6, mode='mock'):
        """One repeatable-read snapshot; bounded terminal cohort, deterministic ordering."""
        from ..control_plane.collection import ExecutionSample
        if not 1 <= limit <= 100 or mode not in ('mock', 'openai'):
            raise ValueError('Invalid Control Plane cohort')
        with self.connect() as conn, conn.transaction():
            conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            rows = conn.execute("""
                SELECT execution_id, document, options, created_at FROM ct_executions
                WHERE document->>'status' IN ('completed','failed')
                  AND document->>'llm_mode' = %s
                ORDER BY created_at DESC, execution_id DESC LIMIT %s
            """, (mode, limit)).fetchall()
            if not rows:
                return []
            histories = {r['execution_id']: [] for r in rows}
            for event in conn.execute('SELECT execution_id,document FROM ct_events '
                    'WHERE execution_id = ANY(%s) ORDER BY execution_id,sequence', (list(histories),)):
                histories[event['execution_id']].append(event['document'])
            return [ExecutionSample(execution=r['document'], options=r['options'], created_at=r['created_at'],
                                    events=histories[r['execution_id']]) for r in rows]
