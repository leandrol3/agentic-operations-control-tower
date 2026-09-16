# Provider externo e continuidade operacional — Aula 2

## Arquitetura preservada

Producer → Redis → Celery → **mesmo LangGraph da Aula 1** → PostgreSQL.
OpenAI é uma dependência dos mesmos nós de interpretação/síntese/julgamento. `llm_runtime.py`
reutiliza OpenAIInterpreter, prompts, schemas e validações da Aula 1 sem modificá-los.
Não existe novo grafo, fila própria, outro provider obrigatório, tracing ou camada de model routing.

Modo/modelo/fallback/falha didática são persistidos em TaskOptions (sem credencial), mantendo a
identidade da operação. Payload/opções diferentes na mesma chave exigem outra version, como antes.
Documentos antigos do banco são lidos com defaults mock. Chaves nunca entram no broker ou no banco.

## Configuração e falhas claras

- Mock: LLM_MODE=mock; nenhuma chave/provider necessário, workflow offline quanto a LLM.
  O fluxo distribuído ainda exige Redis/PostgreSQL locais; offline não significa ausência de broker/banco.
- OpenAI: LLM_MODE=openai e OPENAI_API_KEY (ou fonte privada compatível com Settings da Aula 1).
  OPENAI_MODEL seleciona modelo; ensaio usou gpt-4.1-mini.
- Producer verifica configuração antes de claim/publicação. Worker verifica também: chave ausente
  produz erro explícito persistido, sem fallback silencioso. Modelo do worker deve coincidir com o job.
- Producer/workers devem ser reiniciados com o mesmo perfil. Não misturar configurações na mesma queue.
- Visibility timeout: mock continua 60 s; OpenAI usa 900 s (mínimo aceito 600 s).
  LESSON02_VISIBILITY_TIMEOUT é configuração didática, não um mecanismo de heartbeat/resume.
- SDK conserva timeout de 45 s e max_retries=0 da Aula 1. A camada operacional aplica **uma repetição**
  por request transitória, espera fixa de 1 s. Não soma retries ocultos do SDK.

## Semântica de falhas

Timeout/conexão/HTTP 408/429/5xx → falha transitória → uma repetição → decisão de fallback.
Autenticação/erro de contrato/resposta inválida → sem retry transitório indiscriminado; revisão humana.
Detalhes persistidos são categorias curtas, não corpo da resposta, prompts ou segredos.

**Retry ≠ Redelivery ≠ Fallback ≠ Escalation.** Retry de request não incrementa Execution.attempt;
o detalhe do evento registra request_attempt. Execution.attempt continua sendo tentativa da task.
Redelivery e retry Celery permanecem os mecanismos aprovados das demos mock.

`--llm-failure timeout` intercepta o request antes da rede, desde o Supervisor. Duas falhas artificiais
com uma espera de 1 s tornam a sequência determinística. Não há tokens reais nessas falhas.

### Decisão explícita

- Padrão `--fallback human`: human_review_required, nenhuma recomendação automática.
- Opt-in `--fallback deterministic_reference`: somente após falha transitória, somente envelope do
  case técnico INCIDENT-001. Descarta estado parcial e executa o mesmo grafo com capacidades
  determinísticas. Se validações/estado terminal passarem: degraded_recommendation, mode=degraded,
  motivo explícito, aprovação humana obrigatória. Caso contrário, revisão humana.
- Não é mock nomeado como fallback de produção. A continuidade determinística é autorizada apenas
  para este case de referência com cálculos/políticas/evidências disponíveis.
- Nenhuma compra, transporte ou transferência é executada. Não há decisão de negócio automática.

Outcome=human_review_required pode ter status externo completed: terminou a decisão de encaminhamento,
não a investigação com recomendação. current_step e result.outcome tornam isso explícito. Resultado
humano não inclui Recommendation. Não alegar que uma revisão humana já foi realizada.

## Eventos e duração

`llm.requested`, `llm.failed`, `llm.retry`, `llm.completed`, `llm.fallback_activated`, `llm.degraded`,
`llm.escalated`. Todos emitidos enquanto a execução está running, antes do resultado terminal.
`llm.completed` registra resposta do provider; validação posterior ainda pode recusar seu conteúdo.
Campos input_tokens/output_tokens recebem usage naturalmente retornado, inclusive tokens consumidos
por uma resposta posteriormente rejeitada. Ausência de usage/falha não inventa zero; permanece null.
Sem estimativa de custo, tracing ou lógica de observabilidade.

Execution.duration_ms mede processamento da tentativa, incluindo requests/retry/fallback, excluindo
espera na fila. Eventos ordenam-se pela sequência persistida; especialistas podem intercalar eventos.
`events UUID --llm` mostra apenas a trilha operacional; result/execution mostram outcome e motivo.

## Capacidade e escopo pedagógico

Duas tasks podem executar três especialistas em paralelo cada: dois workers não equivalem a somente
duas requests. A demo de 3 envelopes observa variabilidade, não mede quota nem provoca rate limit real.
As categorias continuam simulando carga de um mesmo case. Não há cinco workflows empresariais novos.

“A inteligência não mudou. Mudou o ambiente operacional ao redor dela.” aplica-se ao modo OpenAI
normal comparado com o workflow da Aula 1. Na degradação, explicar explicitamente que a forma de
sintetizar mudou e a interpretação LLM ficou indisponível.

Antes de SIGKILL/retry/idempotência, concluir trabalhos reais, parar workers, exportar LLM_MODE=mock
+ LESSON02_VISIBILITY_TIMEOUT=60 e reiniciar ambos. Não usar OpenAI nessas demos.

Aula 4: multi-provider routing, cost/quality-aware routing, model health, circuit breakers avançados,
SLO-driven fallback, policies/governance e estratégias de portfolio. Fora desta implementação.
