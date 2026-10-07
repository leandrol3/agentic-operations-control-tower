-- Espelho documental do DDL existente. Não é uma nova migration.

-- Fonte: src/control_tower/distributed/store.py
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

-- Fonte: src/control_tower/runtime/store.py
CREATE TABLE IF NOT EXISTS ct_execution_context (
 execution_id uuid PRIMARY KEY REFERENCES ct_executions(execution_id),
 document jsonb NOT NULL
);
