# Aula 4 — Relatório do ensaio final

**Data:** 04/10/2026 · **Parecer: APROVAR o roteiro para ensaio do professor, com ressalvas pedagógicas abaixo.**
Nenhuma feature, regra, UI ou teste alterado. Nenhum bug impeditivo exigiu correção.
Este é um ensaio técnico real e uma análise de agenda, **não uma aula de quatro horas ministrada a alunos**.
Os tempos de fala são estimativas com orçamento explícito, não medições de aprendizagem.

## A. Baseline

- Branch: `codex/lesson-04-cockpit`.
- Commit do produto: `b3823b2` — identidade L3 e conversa contextual do Maestro.
- Working tree inicial: nenhum arquivo versionado alterado; **24 arquivos pessoais não versionados em `knowledge/`**.
- Esses arquivos foram inventariados por hash e preservados; nenhuma aprovação do ensaio ocorreu na memória pessoal.
- Python com **todas as integrações habilitadas: 546 passed em 22,68 s**, sem skipped.
- Playwright: **9 passed em 7,1 s**.
- TypeScript aprovado; build Docker baseline aprovado com cache; smoke de 12 condições aprovado.
- Lidos: runbooks start/complete/cockpit, scripts de demo/seed/MCP/startup, contratos e projeções relevantes.
- Cockpit final aberto e conferido: 7 agentes, 1 em atenção, Supply 90%/74%/−16 p.p.

A stack foi temporariamente alternada entre mock, falha artificial e OpenAI em memória isolada.
Ao concluir, a stack original OpenAI com memória pessoal foi restaurada, sem novas chamadas LLM.
Volumes PostgreSQL/Redis e os arquivos pessoais foram preservados. O seed do ensaio e os testes
produziram apenas conhecimento sintético em diretório separado.

## B. Agenda final — exatamente 240 minutos

| Bloco | Janela | Min | Composição / margem |
|---|---|---:|---|
| Retomada e problema | 00:00–00:15 | 15 | Contexto, cinco perguntas |
| Service Boundary + MCP | 00:15–00:35 | 20 | Teoria antes da ferramenta |
| Demo 1 HTTP/MCP | 00:35–00:50 | 15 | Comando, leitura, 1 min código, discussão, 2 min margem |
| Registry/Goals/Lifecycle | 00:50–01:15 | 25 | Identidade, contrato, quatro dimensões de estado |
| Demo 2 | 01:15–01:30 | 15 | Registro e exemplo de meta, UI lifecycle, 2 min margem |
| Quality/Economics | 01:30–01:50 | 20 | Status, evidência, consumo/preço/custo |
| Demo 3 | 01:50–02:05 | 15 | Comparação já preparada, 2 min margem |
| Pausa | 02:05–02:20 | 15 | Troca operacional para OpenAI pelo professor |
| Value/SLO/Decision Engine | 02:20–02:45 | 25 | Escopo, limites e autorização |
| Demo 4 | 02:45–03:00 | 15 | Duas fixtures, 1 min código, 2 min margem |
| Control Plane visual | 03:00–03:10 | 10 | Leitura da organização, fontes distintas |
| Maestro conceitual | 03:10–03:20 | 10 | Supervisor vs melhoria da workforce |
| Demo 5 integrada | 03:20–03:38 | 18 | 16 min de percurso explicado + 2 min margem |
| Segundo Cérebro/reflexão | 03:38–03:50 | 12 | 6 min protegidos + até 6 de recuperação |
| Learning Loop/fechamento | 03:50–04:00 | 10 | Hard stop protegido |
| **Total** | | **240** | |

Teoria/contexto explícitos antes do cockpit: 105 min; 20 min conceituais adicionais no cockpit.
A consolidação substitui a soma inviável das agendas históricas, preservando os cinco problemas.
A demo integrada fica em uma janela contínua: não é repetida em cada bloco conceitual.

## C. Tempos reais versus tempo pedagógico

### Método

Comandos: relógio monotônico ao redor do subprocesso, incluindo inicialização do `uv` e consultas.
UI: navegação instrumentada no cliente de navegador; valores incluem a ação de automação e leitura,
não são benchmarks de rendering. Maestro/Compiler/revisão: instante do clique no host até timestamp
persistido no backend local; aproximação de latência ponta a ponta, não só tempo do provider.
Cada medida é uma amostra de ensaio, sem inferência de p95 ou SLA. Máquina aquecida, imagens disponíveis.
O startup idempotente não inclui download/instalação. Prever 45–60 min pré-aula, mais se máquina nova.

| Operação | Expectativa de planejamento | Observado técnico | Tempo pedagógico reservado |
|---|---|---:|---|
| Startup com stack já ligada | até 2 min | 1,785 s | fora da aula |
| Troca para perfil de falha artificial | até 2 min | 15,445 s | pré-aula |
| Troca para OpenAI | até 2 min | 15,557 s | pausa |
| Retorno explícito a mock | até 2 min | 15,460 s | contingência / pré-aula |
| MCP + HTTP + 2 conclusões | até 30 s | 2,933 s | Demo 1: 15 min |
| Registry geral | até 2 s | 0,177 s | dentro de Demo 2 |
| Registry Supply | até 2 s | 0,151 s | dentro de Demo 2 |
| Goal Measurement | até 2 s | 0,129 s | dentro de Demo 2 |
| Geração degraded artificial | até 10 s | 2,188 s | pré-aula |
| Quality normal/degraded | até 2 s | 0,302 s | Demo 3: 15 min com economics |
| Economics normal | até 2 s | 0,189 s | dentro de Demo 3 |
| SLO custo | até 2 s | 0,129 s | dentro de Demo 4 |
| Decision Engine / pipeline / valor parcial | até 2 s | 0,132 s | Demo 4: 15 min |
| Overview por helper | até 2 s | 0,109 s | Demo 5: 1,5 min inicial |
| Snapshot API agregado | até 2 s | 0,042 s | suporte a todas as views |
| Agent 360: seis abas | até 1 s por aba | 0,35–0,46 s por aba | 2,5 min |
| Business Value na aba Economia | até 1 s | 0,373 s (aba incluindo valor) | explicar antes da demo; apontar números |
| Maestro real, diagnóstico/plano | 5–15 s; timeout 45 s | 7,087 s | 3 min |
| Knowledge extraction real | 5–15 s; timeout 45 s | 2,810 s | 1 min de abertura/extração |
| Persistência após revisão explícita | até 2 s | 0,377 s | **3 min de leitura e decisão** |
| Segundo Cérebro / grafo | até 1 s | 0,419 s | 1,5 min |
| Maestro real após aprovação | 5–15 s | 5,562 s | 1,5 min |
| Learning Loop / maturidade | até 1 s | 0,590 s | 1 min na demo + fechamento |
| Maestro mock via API | até 2 s | 0,059 s | fallback |
| Compiler mock via API | até 2 s | 0,061 s | fallback |

**Percurso integrado observado: 182,707 s (3 min 03 s)**, de CTA da atenção até Learning Loop,
incluindo leitura de estados e revisão sintética, sem uma apresentação oral completa.
**Projeção pedagógica: 18 min, teto 20 min**, com as falas e cortes do runbook.
Não há fundamento para garantir 18 min se o professor ler todos os passos, fontes e staffs ou abrir
perguntas longas no meio. A janela de discussão posterior é parte essencial desse desenho.

## D. Demos e resultados efetivamente verificados

### 1. Same Capability, Different Boundary

`demo_lesson04.py boundary`: tools MCP descobertas; POST HTTP e submit MCP da mesma identidade
reutilizaram execution_id (`created=false`); duas execuções reais concluíram em workers; resultados
públicos HTTP/MCP iguais; aprovação pendente; ações não executadas. Nova versão automática a cada ensaio.
MCP usa stdio/SDK real dentro da imagem; não é HTTP disfarçado e não requer LLM nessa demo.

### 2. Registry / Goals / Lifecycle

Sete registros; Supply com tools determinísticas; Finance sem modelo; alvo técnico Registry 100%.
Fixture stable Logistics: atual 100%, gap zero. UI lifecycle: estado atual Ativo e proposta separada,
11 transições representadas, ação indisponível. Nenhum lifecycle foi modificado.

### 3. Normal/degraded e economics

Ambas concluídas, outcomes diferentes, fallback apenas na artificial, aprovação pendente em ambas.
Completude e conformidade desconhecidas. Confiança 0,65 não calibrada. Mock sem tokens/custo inventados.
Falha artificial ocorre antes da rede: não foi usada a chave real e não houve request OpenAI nessa carga.
Troca de perfil preservou as classificações históricas.

### 4. Collect → Interpret → Recommend

Fixture cost: USD 0,02016 acima do SLO 0,01 com conclusão 100%.
Fixture optimize: 66,666667% versus meta 100%, custo crescente, qualidade unknown, proposta Otimizar.
Lifecycle permanece Ativo. Unidade, escopo, prioridade, evidência e aprovação presentes.
Fixtures anunciam fonte sintética. Nenhuma configuração foi alterada para produzir um resultado desejado.

### 5. Cockpit, Maestro, Compiler e memória

- Overview: 1 agente em atenção; Supply 74/90; valor potencial R$ 140 mil; valor realizado não validado.
- Supply: cobertura 37/50, gap −16, contexto degraded 28%; tabs de qualidade, economia, SLO e lifecycle.
- Recomendação Intervir visível; execução indisponível.
- **Duas consultas reais ao Maestro e uma extração real**, com `gpt-4.1-mini`.
- Primeira síntese com 16 evidências; schema aceito e plano proposto persistido.
- Compiler criou `pending_review`, com observações separadas da inferência e referências existentes.
- Candidato lido e aprovado **apenas no ambiente sintético isolado**, com revisor/nota explicitando o ensaio.
- Lista, grafo e feed mostraram aprovação; o incidente não foi aprovado nem executado.
- Segunda consulta usou o novo documento aprovado nas fontes — não apenas existência do arquivo.
- Learning Loop com 12 etapas e régua organizacional entre níveis 3 e 4; nenhum Level 5 operacional.

Título da lição real: “Verificar execução efetiva antes de validar propostas de transferência de estoque”.
A inferência distinguiu proposta de execução física e benefício comprovado. Fonte: caso fictício.
Não se pretendeu validar resultado empresarial ou ensinar a aprovar conteúdo automaticamente.

### Qualidade das respostas reais

Compiler: texto útil, rastreável e com limites explícitos; aprovado apenas como lição sintética.
Maestro: números principais corretos, hipótese separada, fontes válidas, plano longo demais para ler integralmente.
**Ressalvas semânticas:** a primeira resposta tratou latência local como evidência ampla de ausência
de gargalo; atribuiu ao Supervisor uma proposta originada no Decision Engine; sugeriu atualizar uma
lógica de estoque de segurança já existente e usou linguagem de resultado esperado excessivamente assertiva.
Schema/whitelist não detectam essas generalizações. O professor deve contestá-las ao vivo e não endossar
causalidade ou promessa de atingir 90%. Isso reforça o limite entre síntese e autorização.
Não houve execução automática de nenhuma sugestão. Nenhuma alteração de prompt/modelo foi feita nesta tarefa.

## E. Problemas, riscos e pontos a explicar antes

| Achado | Impacto | Tratamento nesta entrega |
|---|---|---|
| Agenda complete já ocupava 240 min sem cockpit | Somar runbooks estoura aula | Nova agenda única, sem apagar documentos históricos |
| Registry target 100% versus cockpit Supply 90% | Parece inconsistência de cálculo | Distinguir conclusão técnica e cobertura de evidência |
| 50 observações Supply vs 6 operações ilustrativas | Aluno pode calcular percentual errado | Declarar populações antes da tela |
| SLO mostra custo pequeno arredondado como 0 | Pode parecer consumo gratuito | Mostrar valor 0,00056 USD na aba Economia; ressalva no roteiro |
| Título Suprimentos pode persistir ao abrir execução/documento pelo Agent 360 | Confusão de localização | Usar breadcrumb/título do documento ou navegar pelo menu |
| Sidebar vira só ícones em janela estreita | Dificulta instrução por nomes | Preparar projeção 1440×900; não redesenhar UI |
| Duas réguas na Learning Loop | Autonomia 1/2 parece contradizer maturidade 3/4 | Explicar autoridade para agir vs maturidade organizacional |
| Repetição de teoria em cada view | Consome tempo sem nova decisão | Conceito uma vez, cockpit como síntese |
| LLM pode generalizar ou propor lógica existente | Proposta soa como diagnóstico confirmado | Confrontar com fontes e código; manter revisão humana |
| Planos/candidatos se acumulam | Seeds contam mais após ensaios | Memória isolada por sessão; não apagar memória pessoal |
| Runbook histórico sugere detalhes demais de chat | Mais chamadas e leitura | Duas sínteses e uma extração na narrativa final |
| Build/provider podem atrasar | Perda de fluidez | Build pré-aula, troca na pausa, conteúdo pré-gerado |

**Não foi encontrado bug impeditivo.** Arredondamento, título persistente e acessibilidade dos ícones
são observações para backlog/revisão posterior, não justificativa para mudar produto aprovado nesta tarefa.
O cabeçalho auxiliar do start (“complete ainda não implementado”) e os limites históricos do complete
(“sem Maestro”) descrevem checkpoints antigos. O runbook final não repete essas afirmações sobre o candidato atual.

Ocorrências do próprio ensaio, sem impacto no produto: o cliente de automação encerrou uma espera
antes da resposta do Maestro; a tela e o plano persistido confirmaram sucesso. A medida usou timestamps.
Um helper temporário esperava o rótulo `mock`, mas o contrato correto é `mock-deterministic`;
a verificação foi corrigida sem alterar produto/testes. Python do sistema não tinha YAML; usou-se o ambiente uv.

### Teoria que merece mais cuidado

1. Service boundary versus protocolo: princípio antes de SDK.
2. Completed versus qualidade semântica, e unknown versus zero.
3. Unidade, janela e origem da medida antes de comparar percentuais.
4. Cost ≠ Value; R$ 140 mil é exposição potencial, R$ 12,5 mil é cenário proposto, benefício não validado.
5. Recomendação do motor, plano do Maestro e revisão do conhecimento são três contratos distintos.
6. Estrutura e proveniência não garantem verdade semântica.
7. Retrieval aprovado melhora contexto do Maestro; não é treinamento nem injeção automática no workflow.

**Pontos rápidos demais se não houver disciplina:** ler/revisar candidato em 30 s; percorrer sete staffs;
explicar duas réguas de maturidade/autonomia somente na última frase. O roteiro reserva leitura e reflexão.

## F. Cortes e recomendações — explícitos, sem remoção dos materiais antigos

| Manter | Reduzir | Retirar da apresentação principal / deixar como consulta |
|---|---|---|
| HTTP/MCP mesma capability | Mecânica MCP a 1 comando + 2 recortes | Segunda demo Codex/MCP interativa na mesma aula |
| Registry, goal e lifecycle distintos | Releitura do Registry no cockpit | Percurso dos sete agentes completos |
| Normal/degraded e unknown | Geração da falha ao vivo: pré-preparar | Repetição de SIGKILL/redelivery da Aula 2 |
| Economics com limites | Pricing a medido/configurado/estimado | Tabela completa de preço e contas de tokens ao vivo |
| Deterministic Decision Engine | Duas fixtures representativas | Executar todas as seis fixtures de ação |
| Supply → Maestro → Knowledge → Loop | Um passo, um staff e uma fonte por vez | Tour por todas as 14 páginas, Next.js/CSS/SQL/Compose |
| Revisão humana e prova de retrieval | Duas consultas reais ao Maestro | Perguntas adicionais de histórico/contexto do roteiro antigo |
| Fechamento de dez minutos | Jaeger apenas se houver pergunta | Novo passeio de tracing da Aula 3 |

Os cortes de demonstrações redundantes liberam pelo menos 30–45 min em relação a tentar executar
integralmente os três roteiros históricos. É estimativa de apresentação, não duração de máquina.
Não se remove conceito central nem demonstração solicitada: muda o nível de detalhe e o momento.

## G. Fallbacks validados

| Falha | Caminho | Validação |
|---|---|---|
| LLM real indisponível | Síntese mock salva em texto; depois modo mock explícito | Maestro mock via API, 0,059 s; gerador mock-deterministic |
| Compiler falha | Candidato do seed, pending_review; revisão continua explícita | Seed local e Compiler mock, 0,061 s |
| UI falha | CLI overview, HTTP API curta e Markdown | Helper/API/arquivos verificados; não exige frontend |
| Docker/API falham | Fixture offline + outputs salvos | Pipeline offline rodou sem consultar serviços |
| Troca de modo | OpenAI → mock com mesma arquitetura | 15,460 s; leitura e geração mock funcionando |
| Resposta LLM semanticamente fraca | Questionar inferência; usar conteúdo preparado | Exemplo real detectado, sem autorizar ação |

Playwright também validou erro recuperável e retry manual de interface em mock.
Não foi provocado timeout real pago nem desligamento destrutivo para “testar fallback”.
A falha de provider da Demo 3 é artificial antes da rede. Não confundir essa resiliência do runtime
com uma troca automática de provider no Maestro: **essa troca automática não existe**.

## H. Regressão final

| Verificação | Resultado | Duração |
|---|---|---:|
| Python full + all integrations | **546 passed**, sem skipped | 22,03 s pytest; 23,287 s processo |
| TypeScript | aprovado | 1,132 s |
| Next build via Docker **sem cache de camadas** | aprovado; compilação + tipos + geração de páginas | 18,498 s total; etapa Next 6,4 s |
| Playwright | **9 passed** | 7,5 s runner; 7,931 s processo |
| Smoke mock | 12 condições, status ok | 0,137 s |
| Compose E2E HTTP/MCP → workers → resultado | aprovado, 2 execuções completed, aprovação pending, actions=false | 2,753 s |
| Health / readiness | alive / ready | 0,015 / 0,016 s |
| Projeção cockpit | 90/74, 1 atenção, 6 operações | aprovada |

A baseline e regressão final não chamaram OpenAI. As três chamadas reais ficaram restritas ao ensaio
explícito do cockpit. O build via Docker executou de fato `next build`, não apenas TypeScript.
Não foram alterados testes para facilitar o ensaio. Os 23 blocos shell passaram em `zsh -n`;
os heredocs Python compilam. Os blocos novos de isolamento, carga segura da chave e fallback
foram executados literalmente, incluindo caminhos com espaços. A agenda soma 240 min.

## I. Entregáveis e Git

- `docs/course/lesson-04-final-runbook.md`: documento único, comandos completos, fala, timing,
  checklist, transições, seis recortes de código, revisão e troubleshooting.
- `docs/course/lesson-04-dry-run-report.md`: este relatório.
- `docs/course/lesson-04/dry-run-evidence/`: outputs curtos e tempos, sem credenciais.
- Pasta local ignorada `artifacts/aula4-*`: memória e fallbacks preparados; caminho em `artifacts/aula4-current.txt`.
- Commit desta entrega: documentação/evidências, sobre `b3823b2`; consultar `git log -1 --oneline`.
- Branch mantida `codex/lesson-04-cockpit`. **Sem push; sem criação/movimentação de tags.**
- Produto, arquitetura, regras, prompts, testes e runbooks históricos intactos.
- Arquivos pessoais de conhecimento permanecem não versionados e fora do commit.

### Parecer final

**APROVAR o roteiro unificado para ensaio do professor.** Há evidência técnica para todas as etapas,
LLM real e contingências. A aula cabe no orçamento de 240 min **seguindo os cortes e os hard stops**.
A demo final tem folga técnica para uma exposição de 18 min; sua duração oral deve ser confirmada pelo
professor com o cronômetro, principalmente na revisão humana e na discussão da síntese do LLM.
Não há necessidade de nova feature para sustentar esta aula. Próxima etapa: revisão pedagógica do professor,
não implementação adicional nem criação de slides nesta tarefa.
