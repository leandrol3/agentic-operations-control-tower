# Arquitetura e evolução
Atual: CLI → Tools → CSV/JSON → contratos Pydantic. Todas as leituras são locais e determinísticas.
Não há rede, agente inteligente, escolha de cenário ou execução operacional neste start.

Destino Aula 1: Event → Supervisor → Supply / Production / Logistics em paralelo →
Finance → Challenger → Recommendation validada → aprovação humana.
LangGraph será introduzido quando o aluno implementar estado, fan-out e fan-in.
OpenAI usará uma interface de provider que também suporte mock; Azure poderá ser adicionado posteriormente.

Estrutura final proposta, com diretórios criados somente quando necessários:
- src/control_tower/{agents,graph,tools,models}: Aula 1; tools/models começam como módulos pequenos.
- workers/: Aula 2, Celery/Redis, jobs, idempotência, retry e estado compartilhado.
- api/, persistence/, config/, docker/, compose.yaml: Aula 3, FastAPI/PostgreSQL e runtime.
- telemetry/, scripts/load/, scripts/chaos/: Aula 4, OpenTelemetry, Langfuse, k6 e fault simulator.
- labs/01_orchestration até labs/04_observability_chaos: roteiros do mesmo sistema.

Tradeoff: start mantém apenas Pydantic em runtime para instalação pequena; não antecipa dependências
LangGraph, OpenAI, Docker, filas ou observabilidade. Não há checkpoints fictícios para aulas futuras.
Dados ficam no checkout e a CLI aceita --root; wheel isolado não inclui o digital twin.
