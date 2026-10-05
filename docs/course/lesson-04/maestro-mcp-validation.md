# Demo 6 — Codex → MCP → Maestro: implementação e validação

Atualização autorizada pelo professor após o ensaio final da Aula 4.
Base: `aeca47b`, branch `codex/lesson-04-cockpit`. Sem push ou tags.

## Implementação

- `src/control_tower/mcp/maestro.py`: adaptador `ask_maestro`, com os contratos Pydantic
  `MaestroRequest`/`MaestroResponse` já usados na API.
- `mcp/server.py --with-maestro`: registro opcional. Sem a flag, catálogo original de três tools intacto.
- `scripts/start_maestro_mcp.sh`: processo stdio dentro do container API já iniciado,
  usando sua configuração, imagem e diretório de conhecimento.
- `scripts/demo_maestro_mcp.py`: cliente SDK de contingência com duas perguntas e saída curta.
- `tests/test_maestro_mcp.py`: quatro regressões específicas, sem chamadas pagas.

```text
Codex → MCP ask_maestro → Conversations → Maestro → MaestroTools
                                            ├→ Control Plane / Registry / Goals / Quality / Economics / SLO
                                            └→ KnowledgeStore: documentos aprovados da mesma fonte
                                            ↓
                                     ImprovementPlan proposto
                                            ↓
                               mesmo filesystem lido pelo cockpit
```

A implementação reutiliza as mesmas classes da API; não chama outro grafo nem reimplementa decisões.
MCP persiste planos propostos, portanto não é uma operação sem efeitos; não grava aprovações,
não executa plano/incidente e não muda lifecycle. Nenhuma tool de aprovação foi adicionada.
O novo catálogo contém as três tools de incidente existentes e `ask_maestro`; a demo chama somente esta última.

Sessões são locais ao processo MCP e separadas das sessões HTTP. `session_id` permite follow-up
na mesma conexão. Planos e conhecimento compartilham storage; histórico de conversa não é global.
O transporte deste LAB é local stdio, não um endpoint remoto para qualquer chatbot.
Codex e Maestro são duas camadas de inferência/autenticação; a chave do Maestro fica no container.

## Validação real — Codex como cliente

Cliente: Codex CLI `0.155.0-alpha.16.4`, autenticado pelo ChatGPT.
Configuração MCP temporária com `-c`; sessão `exec --ephemeral --ignore-user-config --approve-for-me`.
Nenhum cadastro global foi modificado e nenhum bypass de segurança foi usado.
A sessão interativa `/mcp` e a interface Desktop não foram operadas nesta validação.

**Resultado:** duas chamadas reais a `ask_maestro`, ambas concluídas, mesma sessão;
Maestro em `openai:gpt-4.1-mini`. **53,278 s no total**, incluindo startup, modelo do Codex,
aprovações automáticas normais, inferências do Maestro e resposta final do cliente.
Não é uma medida isolada de latência OpenAI nem garantia de execução futura.

1. “Como posso melhorar o agente de Supply?” → diagnóstico 74% versus meta 90%, hipótese,
   plano proposto e fontes, com aprovação humana obrigatória.
2. “Que conhecimento aprovado sustenta essa proposta?” → reutilizou sessão e citou documentos
   aprovados, incluindo **“Verificar execução efetiva antes de validar propostas de transferência de estoque”**,
   aprovado no ensaio sintético anterior.

Planos `plan-519a4d9460ec42a1aa0221dd25fb9ee4` e `plan-4a59db696d9e48fbb0cd04c6ca377ace`
confirmados também no snapshot HTTP do cockpit, após encerramento do cliente.
Não houve nova aprovação de conhecimento, submissão de incidente ou execução operacional nessa sessão.
Memória de ensaio isolada; a memória pessoal não foi enviada ao provider nem modificada.

Evidências curtas: [codex-real.json](maestro-mcp-evidence/codex-real.json) e
[resumo do cliente](maestro-mcp-evidence/codex-answer.txt). Sem chave, prompts internos ou chain-of-thought.

## Mock e compatibilidade

Cliente SDK real sobre stdio: duas consultas em mock, aproximadamente 0,11 s e 0,10 s;
mesmo contrato, mesmo serviço, aprovação obrigatória e conteúdo aprovado consultado.
Mock não chamou OpenAI. O cliente Codex em si depende de sua própria disponibilidade/autenticação;
o fallback SDK mock não depende do modelo do Codex.

Quatro novos testes:

1. MCP real em memória, sessão contínua, exclusão de candidato pendente, inclusão após revisão
   explícita exclusivamente sintética no teste; lifecycle permanece ativo.
2. Validação de request e sanitização de erro do provider; nenhum plano parcial salvo.
3. Fonte durable não reutiliza conhecimento didático.
4. API HTTP e MCP produzem os mesmos diagnóstico, passos, evidências e fontes em mock.

Regressão final:

- **550 testes Python aprovados em 21,98 s**, incluindo todas as integrações opt-in; sem skipped.
- **9 testes Playwright aprovados em 8,1 s**.
- TypeScript aprovado.
- Imagem de runtime reconstruída e iniciada; build cockpit reutilizou cache (frontend não mudou).
- Smoke mock: 12 verificações aprovadas.
- Demo original HTTP/MCP concluída: três tools originais, mesmo UUID na idempotência,
  resultados iguais, aprovação pendente e nenhuma ação.
- `git diff --check`, sintaxe shell dos blocos copiáveis e soma da agenda verificados.

## Ajuste pedagógico

O [runbook final](../lesson-04-final-runbook.md) agora tem índice de **Demos 1 a 6**.
A demonstração Codex/MCP encerra o percurso aplicado, sem sufixos na numeração.

| Horário | Bloco |
|---|---|
| 03:00–03:08 | Control Plane visual |
| 03:08–03:15 | Maestro conceitual |
| 03:15–03:33 | Demo 5 — cockpit integrado |
| 03:33–03:40 | **Demo 6 — Codex → MCP → Maestro** |
| 03:40–03:50 | Segundo Cérebro/reflexão |
| 03:50–04:00 | Learning Loop e fechamento |

As três primeiras horas permanecem. **240 minutos no total**; 18 min para Demo 5 e 7 min para Demo 6.
A validação técnica de 53 s deixa espaço para duas perguntas e comparação, mas os sete minutos
incluem explicação e não foram medidos como fala integral do professor.

Roteiro inclui registro do servidor, autenticação, prompts copiáveis, variante `codex exec` testada,
comandos de fallback SDK/mock e esclarecimento das sessões separadas. A conexão fica pronta antes da aula.
Manter: prova de memória aprovada acessível por outra interface e a fronteira de autorização.
Cortar se atrasar: segunda pergunta, detalhes de configuração e releitura de fontes; nunca o fechamento.
As ressalvas semânticas do ensaio anterior continuam: síntese do LLM não confirma causalidade nem valor realizado.

**Parecer: APROVAR a Demo 6 para o ensaio do professor.** Mesma capacidade de gestão por outra boundary,
sem ampliar autoridade de execução ou adicionar outro sistema de agentes.
