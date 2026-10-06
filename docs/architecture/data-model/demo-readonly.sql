BEGIN READ ONLY;
\pset pager off
\dt public.ct_*
\d public.ct_executions
\d public.ct_events
\d public.ct_execution_context

SELECT execution_id, document->>'incident_id' AS incident,
       document->>'status' AS status,
       document->>'worker_id' AS worker,
       document->>'duration_ms' AS duration_ms,
       attempts, event_sequence
FROM ct_executions
ORDER BY created_at DESC, execution_id DESC LIMIT 5;

SELECT e.sequence, e.document->>'attempt' AS attempt,
       e.document->>'event_type' AS event,
       e.document->>'agent_id' AS agent,
       e.document->>'status' AS status
FROM ct_events e
WHERE e.execution_id = (
  SELECT execution_id FROM ct_executions
  ORDER BY created_at DESC, execution_id DESC LIMIT 1
)
ORDER BY e.sequence;

SELECT document->>'status' AS execution_status,
       document->'result'->>'outcome' AS outcome,
       document->'result'->'approval'->>'status' AS approval,
       document->'result'->'approval'->>'actions_executed' AS acted
FROM ct_executions
ORDER BY created_at DESC, execution_id DESC LIMIT 5;

SELECT e.execution_id, c.document->>'trace_id' AS trace_id,
       c.document->>'correlation_id' AS correlation_id
FROM ct_executions e LEFT JOIN ct_execution_context c
  ON c.execution_id = e.execution_id
ORDER BY e.created_at DESC, e.execution_id DESC LIMIT 5;
COMMIT;
\q
