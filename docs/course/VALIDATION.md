# Validação de lesson-01-complete

## Revisão mock + OpenAI — 15/09/2026

- Suíte completa offline: **169 testes passaram**, 7,65 s; mock, contratos e provider controlado.
- Smoke mock: 12 verificações passaram. E2E mock preserva o estado de negócio do exemplo anterior.
- E2E real com gpt-4.1-mini: seis respostas estruturadas, cenário D, custo R$ 12.500,
  awaiting_approval, actions_executed=false. Acesso habilitado pelo professor após erro inicial 403.
- CLI real `show INCIDENT-001 llm-decisions`: código 0; view de 17 linhas, até 94 colunas.
- Script compare_modes.py: código 0; Investigation e FinanceReport idênticos entre mock e OpenAI.
  Comparação observada em 8,61 s; não é benchmark. Exemplo gravado em examples/incident-001-modes-comparison.txt.
- Saída inválida/incompleta, recusa, timeout, plano incompleto, referência desconhecida, alteração
  de número e cenário inadmissível bloqueiam o fluxo; não há fallback silencioso nem aprovação automática.
- Valores monetários mantêm validação Decimal local; schema de transporte LLM usa strings para evitar
  a união/regex decimal complexa. Respostas passam também pela validação contra cálculos determinísticos.
- Oito views mock: 10–16 linhas, até 94 colunas; nova view OpenAI gravada também cabe em 20 × 96.
- Runbook mantém 240 minutos e inclui comparação de oito minutos no bloco 10B.
- Dados, tools, models, cenários, Finance e regras determinísticas de Challenger não foram modificados.
- Sem novas dependências de infraestrutura. SDK OpenAI instalado; modo mock continua sem rede.
- Credencial .keys fora do Git; tags start/complete preservadas. Publicação na main autorizada pelo professor.


## Revisão de experiência de aula — 15/09/2026

- Suíte completa: **120 testes passaram** em 7,05 s.
- Smoke: 12 verificações passaram; fluxo completo em mock terminou em awaiting_approval.
- Cenário D: custo incremental R$ 12.500; multa evitada R$ 16.000; nenhuma ação executada.
- Sete views testadas: summary, state, specialists, coordination, scenarios, challenger e recommendation.
- Testes verificam limite de 20 linhas por 96 colunas e ausência de conclusão antecipada nas views iniciais.
- Arquitetura central, agentes, cálculos financeiros e contratos permanecem iguais à tag aprovada.
- Materiais offline incluem SVG, trechos de código e representações textuais de fallback.
- HTML/SVG não tiveram inspeção visual no navegador integrado: acesso a arquivo local foi bloqueado.
  As dimensões das saídas de terminal foram verificadas pelos testes.
- Publicação na main autorizada pelo professor; nenhuma tag criada ou movida.

## Validação anterior do checkpoint técnico

- Suíte completa: 91 testes passaram em macOS ARM64, Python 3.12.3 e LangGraph 1.2.11.
- Smoke: 12 checks do fixture oficial passaram.
- Reprodução em cópia limpa sem .venv/.env: uv sync --locked --offline (cache local), suíte de 91 testes,
  doctor/incident/tools/smoke/graph, run normal/JSON/sequencial/paralelo e falha simulada passaram
  com os códigos esperados. JSON gravado coincide com o estado de nova execução.
- Instalação inicial do LangGraph foi feita com rede; reprodução limpa utilizou cache já preparado.
- E2E `run INCIDENT-001`: saída 0, cenário D, custo incremental 12.500 BRL,
  multa evitada 16.000 BRL, estado awaiting_approval, solicitação pending, nenhuma ação executada.
- Falha `--fail-specialist logistics`: saída 1 esperada, demais resultados preservados,
  join bloqueado, Finance/Challenger/Recommendation/Approval ausentes.
- Paralelismo: teste com Barrier exige que os três ramos iniciem antes de qualquer um terminar;
  join executa uma vez, após todos, e antes de Finance. Modo sequencial produz o mesmo estado final.
- Observação manual com 500 ms artificiais por especialista: 0,515 s paralelo e 1,531 s sequencial
  em uma execução local. Não é benchmark nem expectativa de tempo em outras máquinas.
- JSON final determinístico entre invocações; a ordem dos eventos concorrentes/tempos pode variar.
- Teste bloqueia socket.connect e create_connection; mock funciona mesmo com tracing solicitado
  por variável de ambiente. O workflow força tracing desabilitado.
- Regressões cobrem estado/saídas inválidas, routing, especialista ausente/falhando, falta de capacidade,
  alocação sem dupla contagem, datas/multas A–D, revisão independente, políticas e limites inclusivos,
  aprovação obrigatória e imutabilidade dos dados operacionais.
- Exemplos gravados em docs/course/examples e diagrama extraído do grafo real em docs/architecture.
- Não testado: OpenAI (não implementado), Windows/Linux, infraestrutura de aulas seguintes.
- Revisão concluída e publicação autorizada pelo professor. Tag lesson-01-start preservada em 5dc5fa09782c74dd61fe83b56a6c6dc8b0311afb.
- Start revisado aprovado registrado em 171c324 para comparação separada.

## Histórico da validação do start


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
