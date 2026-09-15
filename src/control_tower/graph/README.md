# Grafo explícito da Aula 1

state.py define estado compartilhado Pydantic. Supply, Production e Logistics escrevem em canais
separados; não é preciso um reducer que mescle resultados concorrentes no mesmo campo.
workflow.py define fan-out e `add_edge(list(SPECIALISTS), 'consolidation')` para esperar todos.
Consolidação valida presença/sucesso; Finance só é chamado com evidências completas.
Challenger → Recommendation → Human Approval termina com solicitação pendente, sem executar ações.

`uv run control-tower graph` gera Mermaid a partir do grafo real.
`uv run control-tower run INCIDENT-001 --sequential` usa as mesmas funções com arestas sequenciais
para comparação didática. Não há checkpoint persistente, retomada ou execução operacional.
