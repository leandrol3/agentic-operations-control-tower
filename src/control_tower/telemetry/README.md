# Contrato de telemetria — start

- trace_id: identidade técnica de correlação; 32 hex, não um span.
- correlation_id: identidade externa/da sessão do professor.
- execution_id: UUID lógico durável da Aula 2.
- incident_id: envelope de entrada; o workload ainda é INCIDENT-001.
- worker_id: hostname + PID do consumidor, pode mudar em outra tentativa.

API → associação PostgreSQL → headers Celery → ContextVar do worker → log.
A primeira associação persiste e prevalece em duplicatas. Não há traceparent nem árvore de spans.
`context.py` valida/carrega identidade; `logging.py` projeta human/json; `tracing.py` prepara SDK;
`config.py` documenta seis métricas futuras, sem alegar que já estão sendo coletadas.

OTEL_ENABLED=false: nenhum exporter/thread/request. true sem endpoint: SDK local sem export.
true com endpoint: exporter OTLP/HTTP preparado, mas a aplicação ainda não emite spans no start.
Não autoinstrumentar todas as bibliotecas agora. Mock não faz request LLM.

ExecutionEvent ≠ telemetry signal. Eventos são fonte durável; log pós-tentativa é uma projeção
operacional, pode repetir em duplicata ou faltar se processo morrer. Não substitui os eventos.
Ver [decisões e limites](../../../docs/course/lesson-03/contracts.md).
