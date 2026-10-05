# Aula 4 — materiais do professor

- [Roteiro slide a slide em PDF](Aula-4-Roteiro-do-Professor-Slide-a-Slide.pdf): 111 páginas, 70 slides, seis demos, falas, comandos, recortes de código e 19 capturas reais em 17 fichas.
- [Comandos de apoio](Aula-4-Comandos-de-Apoio.txt): copiar apenas o bloco indicado no roteiro; não executar o arquivo inteiro. Há alternativas e mudanças de modo.
- [Captura de metas de Suprimentos](Aula-4-Control-Plane-Metas.png).
- [Runbook principal](../../lesson-04-final-runbook.md): seis demos em 240 minutos, com o cockpit como interface principal nas Demos 2–4.

## Versão e reprodução

Edição de 05/10/2026, baseada no commit `8035e27` e na revisão pedagógica do runbook publicada junto destes materiais. O PDF registra a situação anterior à publicação; a referência à revisão local é histórica.

Use a branch `codex/lesson-04-cockpit`. As branches `codex/lesson-04-start` e `codex/lesson-04-complete` preservam estágios anteriores para comparação. Nenhuma tag foi criada ou movida nesta publicação.

As capturas usam `LLM_MODE=mock` e fonte **Cenário didático**. A preparação do roteiro descreve como habilitar OpenAI para Maestro/Compiler, sem expor a chave. Os números sintéticos não são consumo real de provider; planos são propostas e aprovação de conhecimento não autoriza ação empresarial.

Os dados pessoais dos ensaios em `knowledge/` não fazem parte da entrega. Os seeds didáticos versionados continuam disponíveis. Prepare a memória isolada seguindo o runbook antes da aula.

## Verificação antes da publicação

Em 05/10/2026: suíte Python em mock **529 passed, 21 skipped** (18,85 s); smoke mock **12 verificações**; `npm --prefix web run typecheck` aprovado. Os 21 skips são testes de integração que não foram habilitados nesta rodada. A validação anterior do candidato está nos relatórios da Aula 4; esta publicação não reivindica novo ensaio OpenAI nem regressão Playwright.

PDF conferido: 70 cenas, 111 páginas, agenda de 240 minutos e sintaxe dos comandos validada.
