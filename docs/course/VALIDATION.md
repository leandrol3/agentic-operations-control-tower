# Validação de lesson-01-start

- Ambiente observado: macOS ARM64, Python 3.12.3, uv 0.7.6.
- `uv sync` gerou uv.lock e instalou as dependências.
- `uv run pytest`: 45 testes passaram na revisão do start.
- `uv run control-tower smoke`: status ok, INCIDENT-001, três ordens relacionadas, impacto não avaliado e 12 checks de prontidão.
- Cópia limpa sem .venv e sem .env: `uv sync --locked --offline` instalou a partir do cache;
  `.env.example` foi copiado para `.env`, pytest e doctor/incident/tools/smoke passaram.
- Instalação inicial com rede foi validada no checkout de trabalho; instalação limpa usou cache.
- Testes cobrem demanda, estoque/reservas, alternativas, rotas, multas, entradas inválidas,
  referências quebradas, duplicação de estoque, contrato de aprovação e configuração da CLI.
- O modo mock não importa SDK de LLM nem necessita de chave.
- Windows/Linux, Docker, API e execução com LLM real não foram testados: infraestrutura e
  provider real estão fora do escopo deste checkpoint.
- README diferencia recursos existentes de roadmap e documenta premissas do dataset.
- Routing, retries e transições do grafo serão testados quando forem implementados no complete.

A inspeção inicial encontrou repositório remoto vazio. Commit e tag de entrega devem ser conferidos
em `git log --oneline` e `git tag --list`, respectivamente; este documento não atesta publicação remota.

## Revisão pedagógica: demonstração guiada

- Validada nova cópia limpa, sem .venv/.env: instalação com lock e cache offline, suíte completa,
  doctor, incident, tools e smoke passaram.
- Comandos de demonstração `pytest -k incomplete` e `pytest -k invalid_recommendation` passaram
  na cópia limpa. Casos de falha usam fixtures temporários e preservam dados oficiais.
- Regressões adicionadas: fornecedor alternativo ausente, estoque de Campinas ausente, rota padrão/
  expressa ausente, ordem relacionada ausente, cada tabela vazia, cada arquivo obrigatório ausente,
  cabeçalho incompleto e entrega incompatível com um dia de transporte após produção.
- Testes verificam que smoke falha com código 2 sem emitir JSON de sucesso em fixture incompleto.
- CLI distingue related_orders e impact_status: not_assessed; não realiza simulação de impacto.
- Agenda do runbook soma 240 minutos. Demos 1–4 são executáveis; 5–8 descrevem progressão futura
  e não foram apresentadas como implementadas/testadas.
- Configuração, datasets, models e dependências preservados. Mudança temporal está na validação
  das relações e documentação; dados existentes já atendem à convenção.
- Tag publicada lesson-01-start preservada em 5dc5fa09782c74dd61fe83b56a6c6dc8b0311afb.
  Ajustes locais na branch codex/lesson-01-start-guided-demo, preparados para revisão sem publicação.
