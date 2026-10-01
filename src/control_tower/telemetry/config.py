"""Instruments reais do complete; nunca usar IDs individuais como labels."""
METRICS = {
    'executions.started': ('counter', '1', 'Tentativas iniciadas após claim'),
    'executions.completed': ('counter', '1', 'Tentativas concluídas'),
    'executions.failed': ('counter', '1', 'Tentativas falhas, inclusive antes de retry'),
    'execution.duration': ('histogram', 's', 'Tentativa sem espera na fila'),
    'llm.calls': ('counter', '1', 'Requests por tentativa / marcadores mock'),
    'llm.failures': ('counter', '1', 'Falhas de request'),
    'llm.tokens.input': ('counter', '1', 'Usage reportado pelo provider'),
    'llm.tokens.output': ('counter', '1', 'Usage reportado pelo provider'),
}
