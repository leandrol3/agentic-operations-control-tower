# Publicação autorizada — Aula 4

Em 05/10/2026, o professor autorizou atualizar o GitHub com a implementação e os materiais
aprovados. Nesta publicação, as branches da Aula 4 são preservadas e a integração com
main será apresentada em PR, sem merge automático.
Preservar tags/checkpoints e excluir dados pessoais de ensaios e credenciais.
Esta autorização substitui as restrições históricas de push abaixo; não autoriza ACT.

# Escopo vigente — Demo 6: Codex → MCP → Maestro

Autorizado em 04/10/2026: adaptador MCP opcional para o Maestro existente e roteiro final com
seis demos em 240 minutos. Mesmas fontes/regras/contratos, sem aprovação ou ACT via MCP.
Preservar as três tools e checkpoints anteriores; sem push ou tags.

# Escopo vigente — candidato lesson-04-cockpit

Autorizado em 03/10/2026: Presentation Layer pt-BR, cockpit Next.js separado, projeções backend,
Maestro com fontes e planos, Knowledge Compiler e Segundo Cérebro Markdown com revisão humana.
Preservar runtime/checkpoints; sem ACT autônomo, auto-modify, auto-deploy, push ou tags.
Esta autorização substitui limites históricos incompatíveis abaixo. Parar para revisão.

# Escopo vigente — candidato lesson-04-complete

Autorizado em 02/10/2026: Collect → Interpret → Recommend; Goal Measurement, Business Value
parcial, SLOs/thresholds didáticos, tendências simples, lifecycle state machine pura,
triggers e Decision Engine determinístico; API/cockpit read-only, fixtures identificadas.
Preservar runtime, Aulas 1–3 e start. Sem ACT, auto-remediation, auto-modify, push ou tags.
Esta autorização substitui limites históricos incompatíveis abaixo. Parar para revisão.

# Escopo vigente — candidato lesson-04-start

Autorizado em 01/10/2026: MCP reutilizando capability HTTP, Registry local com Business Goals,
Quality e Economics derivados do histórico durável. Preservar core, contracts e infraestrutura
Aulas 1–3. Sem decision engine, SLO, lifecycle actions, Aula 4 complete, push ou tags.
Esta autorização substitui limites históricos incompatíveis abaixo. Parar para revisão.

# Escopo vigente — fechamento e congelamento lesson-03-complete

Autorizado em 30/09/2026: somente evidências/documentação, regressão final, correções indispensáveis,
commit final e tag anotada local `lesson-03-complete` após validação. Sem push, features, refatorações
ou Aula 4. Professor aprovou arquitetura/demos, smoke OpenAI real e rehearsal integral.
Esta autorização substitui restrições históricas incompatíveis abaixo; demais limites permanecem.

# Escopo vigente — candidato lesson-03-complete
Autorizado em 28/09/2026: tracing OTel real, W3C, spans semânticos, Collector + Jaeger,
métricas básicas e Demos6–9. Preservar start, core/regras Aulas1/2, HTTP/health/readiness.
Não criar/mover tags, não publicar, não iniciar Aula4. Parar para revisão.
Esta autorização substitui apenas as restrições históricas incompatíveis abaixo.

# Escopo vigente — candidato lesson-03-start
Autorizado pelo professor em 24/09/2026: somente API mínima, runtime/container, settings,
health/readiness e contratos de telemetria/correlação. Sem tracing distribuído completo.
Esta seção prevalece sobre proibições históricas de API/telemetria abaixo.
Aulas 1/2 congeladas: adicionar camadas, preservar grafo/tasks/tools/store e regressões.
Compose base preservado; override adiciona runtime. Não criar/mover tags nem publicar sem pedido.
Parar para revisão; detalhes em docs/course/lesson-03-runbook.md e lesson-03/contracts.md.

# Instruções de engenharia
Leia completamente docs/course/ antes de alterar código. PROJECT_CONTEXT.md é a fonte de requisitos.
Preserve decisões e checkpoints existentes; não mova tags aprovadas silenciosamente.
Escopo atual: candidato lesson-02-complete. Aula 1 congelada no commit 8fbc4fc.
Rodada atual: Celery/Redis e PostgreSQL reais; preservar comportamento do start aprovado.
Preserve código/dados/testes/materiais da Aula 1, salvo despacho aditivo de novos comandos da CLI.
Sem checkpoint/resume por nó, API ou telemetria. Não criar tags sem revisão.
Não publicar esta revisão sem solicitação. Não transformar a aula em live coding.
Tag lesson-01-start permanece intacta; revisão aprovada do start está no commit 171c324.
Um único sistema evolui nas quatro aulas; não criar quatro aplicações.
Python 3.12, uv, Pydantic e LangGraph. Mock offline e OpenAI via OPENAI_API_KEY; OPENAI_MODEL seleciona modelo.
Use contratos tipados, módulos pequenos, Decimal para dinheiro e cálculos determinísticos.
Agentes acessam capabilities em tools, nunca CSVs diretamente. Aprovação humana permanece obrigatória.
Modo mock deve funcionar offline após instalação, sem chave e sem chamadas pagas.
Não adicione infraestrutura futura antes de surgir a necessidade didática.
Disciplina: 16 horas, quatro aulas de quatro horas. Alunos NÃO programam durante as aulas.
Método: contexto → teoria → problema → demonstração selecionada → discussão → reflexão.
Reservar 60–80 min para contexto e teoria. Código só quando esclarece decisão arquitetural.
Otimize demonstração ao vivo, comparação visual/Git entre checkpoints e reprodução posterior.
Preserve datasets, models, tools, CLI, fixtures, configuração, testes e mock prontos; evite boilerplate ao vivo.
Labs são Guided Demo / Observation Guides; docs/course/lesson-01-runbook.md orienta o professor.
Execute uv run pytest e uv run control-tower smoke; confira README em ambiente limpo antes de tags.
Use commits pequenos e significativos. Nunca commite .env ou credenciais; se encontrar segredo,
pare e informe antes de publicar. Não publique mudanças sem solicitação.
Documente limites honestamente: este laboratório ensina engenharia de produção, não é produção real.
