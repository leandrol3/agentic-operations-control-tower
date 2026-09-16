# Contratos preparados — lesson-02-start

## Execution

| Campo | Tipo / significado |
|---|---|
| execution_id | UUID de uma execução física |
| incident_id | Identidade do envelope sintético |
| status | queued / running / completed / failed |
| started_at | Data/hora com fuso; null em queued |
| completed_at | Data/hora com fuso; apenas terminal, não anterior ao início |
| current_step | null em queued; capacity_wait no início e awaiting_approval/failed ao terminar |
| attempt | Inteiro ≥1; permanece 1 no start, sem retry automático |
| worker_id | PID + thread local; null em queued |
| error | Somente failed exige descrição de falha |
| workflow_status | awaiting_approval / blocked / null; distinto de status externo |

[Exemplo real de Execution](execution-example.json) · [trilha de eventos](events-example.md).

O histórico de passos internos aparece nos eventos; não há state store que possa ser consultado
durante a execução. Completed não significa compra autorizada nem incidente de negócio resolvido.

## ExecutionEvent

| Campo | Tipo / significado |
|---|---|
| execution_id / incident_id | Correlação com a execução e envelope |
| agent_id | Nó do grafo, intake ou worker |
| event_type | execution_queued/started/completed/failed ou step_started/completed/failed |
| timestamp | Data/hora com fuso, emitida em UTC |
| status | Status externo da execução no momento do evento |
| duration_ms | Duração monotônica não negativa; null quando ainda não mensurável |
| sequence | Contagem crescente por execução, começando em 1 |
| attempt | Tentativa correlacionada, 1 no start |
| input_tokens / output_tokens | Inteiros não negativos, null nesta entrega |
| estimated_cost | Decimal não negativo com duas casas; BRL por convenção do curso; null |
| quality_score | Entre 0 e 1; null |
| business_outcome | Texto opcional; null |

Campos futuros são placeholders de contrato, não observabilidade implementada nem estimativas inventadas.
Todos os modelos rejeitam campos desconhecidos. Tipagem valida estrutura, não entrega durável.

## IdempotencyIdentity

Campos: incident_id, operation (`analyze-reference`), version (`v1`). Strings vazias são rejeitadas.
Chave: `idem-v1-` + SHA-256 do JSON canônico `[incident_id, operation, version]` em UTF-8.
Separação JSON evita ambiguidades de concatenar strings; `hash()` do Python não é usado.

- Duas entregas da mesma identidade → mesma chave, mesmo entre processos.
- Outra operação, incidente ou versão → outra chave.
- execution_id, worker_id e attempt não entram na identidade lógica.
- Correção do payload sob o mesmo incident_id exige decidir se a operação deve receber outra versão.
- Não há consulta/insert atômico nem proteção contra duplicatas neste start.
- Um retry pode criar uma tentativa física; a reivindicação atômica da chave ainda será desenhada.
- Não prometer exactly-once: uma chave estável sozinha não implementa nenhuma garantia de entrega.

## Persistência: o que há e o que falta

Há coleta de eventos em memória e export opcional após o lote. Não há banco conectado,
checkpoint, recuperação ou continuidade entre processos. Redis/PostgreSQL saudáveis são apenas
infraestrutura preparada. Reiniciar o processo perde o que não foi exportado, e nem o export é retomável.

Relógios distintos: created_at do incidente é data fictícia fixa do case; started_at/completed_at e
event timestamp são relógio real do ensaio. Não subtrair esses relógios para medir latência.
