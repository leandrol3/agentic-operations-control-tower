"""Contratos de métricas, ainda sem instruments/export automático no start."""
METRICS = {
    'http_requests_total': ('counter', '1', 'Requisições HTTP por rota/método/status'),
    'executions_total': ('counter', '1', 'Execuções lógicas novas, não mensagens duplicadas'),
    'execution_failures_total': ('counter', '1', 'Execuções terminadas em failed'),
    'queue_submission_total': ('counter', '1', 'Publicações confirmadas pelo producer'),
    'execution_duration_ms': ('histogram', 'ms', 'Duração da tentativa, exclui fila'),
    'llm_calls_total': ('counter', '1', 'Chamadas ao provider, inclui retry'),
}
# IDs individuais nunca serão labels de métricas: cardinalidade ilimitada.
