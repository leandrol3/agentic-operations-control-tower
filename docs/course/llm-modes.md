# Aula 1 — LLMs interpretam e julgam. Código determinístico mede e valida.

## Modos e fronteira exata

O mesmo grafo é construído para os dois modos. `mock` é o fallback offline e determinístico;
`openai` executa seis chamadas pela Responses API. Não há serviços novos nem execução operacional.

| Etapa | Código determinístico nos dois modos | LLM somente em openai |
|---|---|---|
| Supervisor | Escopo do incidente; nomes válidos; plano completo; roteamento | Interpretação; escolha de papéis; perguntas em InvestigationPlan |
| Supply | Estoque, reservas, fornecedores e quantidades pelas tools | SpecialistSynthesis: resumo, referências e incerteza |
| Production | Ordens/clientes e demanda pelas tools | SpecialistSynthesis: resumo, referências e incerteza |
| Logistics | Rotas, capacidade, frete e prazo pelas tools | SpecialistSynthesis: resumo, referências e incerteza |
| Join | Barreira dos três ramos; presença e validade das evidências | Nenhum |
| Finance | Alocações A–D, datas, custos, multas e proposta de menor custo | Nenhum |
| Challenger | Validação aritmética, temporal e de políticas; bloqueios | ChallengerJudgment: premissas frágeis e informação insuficiente |
| Recommendation | Elegibilidade; valores conferidos; ação canônica e riscos preservados | RecommendationDecision: preferência entre admissíveis, Recommendation e justificativa |
| Human Approval | pending, awaiting_approval, actions_executed=false | Nenhum |

Saídas LLM são Pydantic, com `extra=forbid`. Texto do modelo nunca substitui Inventory, SupplyEvidence,
ProductionEvidence, LogisticsEvidence ou FinanceReport. Sínteses ficam em campos separados do estado.
Nenhuma cadeia de raciocínio é solicitada, registrada ou apresentada; apenas resumos e justificativas.
`LLMRecommendation` herda Recommendation e simplifica somente o schema monetário de transporte para
strings. A validação Money/Decimal (sinal, precisão e casas decimais) continua ativa, seguida da
conferência contra valores calculados. Isso evita enviar à API a união/regex decimal gerada pelo Pydantic.

### Limites explícitos

- Este fixture exige Supply + Production + Logistics para produzir A–D. O modelo escolhe papéis e
  perguntas; omissão/duplicação/papel desconhecido bloqueia antes do fan-out. Não há join variável.
- A execução paralela preserva canais de escrita independentes, inclusive das três sínteses.
- Challenger LLM é consultivo: acrescenta até três achados, nunca remove políticas nem redefine custos.
  Alertas ficam na revisão e são preservados na recomendação. Não concedem autorização operacional.
- Recommendation pode preferir B a D, por exemplo, para evitar atraso residual. O custo de B continua
  R$ 20.250 e o de D R$ 12.500. Não force mesma escolha para alegar determinismo do LLM.
- Incident_id, custo, multa evitada, atraso, confiança didática e aprovação são conferidos contra
  templates determinísticos. Divergência bloqueia. A ação final é o texto canônico do cenário escolhido;
  a justificativa do LLM permanece separada e identificada.
- `confidence=0.65` permanece constante didática, sem calibração estatística, inclusive em openai.
- Pydantic e conferência dos números não garantem a veracidade de cada frase gerada. Revisão humana
  continua necessária, inclusive para riscos ou justificativas indevidas.
- Falhas, recusa, timeout ou saída inválida bloqueiam. Não existe fallback silencioso nem retry.
  Timeout de 45 s por chamada; seis chamadas, três delas paralelas. Não é orçamento global de 45 s.
  Limite de resposta: 2.400 tokens por chamada; 6.000 na Recommendation, que inclui o contrato completo.
  Esses limites não são estimativas de consumo; a view exibe somente resumos curtos.
- SDK OpenAI é importado somente ao criar o provider real. Mock não lê o arquivo de chave nem faz rede.
  As dependências precisam estar instaladas previamente para reproduzir offline.

## Configuração antes da aula

`uv sync --locked` instala o SDK. Configure `LLM_MODE`, `OPENAI_MODEL` e `OPENAI_API_KEY`.
Ambiente tem precedência sobre `.env`. Padrões: mock e gpt-4.1-mini.
O modelo selecionado precisa suportar Responses API e Structured Outputs.

A chave pode estar em `.env` ignorado, no ambiente ou em `.keys` na raiz do checkout.
O arquivo aceita `OPENAI_API_KEY=...` ou somente o valor. Para outro local, informe
`OPENAI_API_KEY_FILE`; não há busca implícita em diretórios pais. Nenhum segredo vai ao grafo ou logs.
Arquivos `.keys` e `.keys.*` estão no `.gitignore`. `OPENAI_API_KEY` tem precedência sobre o arquivo.
O provider usa o endpoint oficial fixo, `store=false`, sem tracing ou ferramentas remotas.
As evidências fictícias e os contratos necessários são enviados à OpenAI no modo real.

```bash
LLM_MODE=mock uv run control-tower show INCIDENT-001 llm-decisions
LLM_MODE=openai OPENAI_MODEL=gpt-4.1-mini uv run control-tower show INCIDENT-001 llm-decisions
# Se .keys estiver na pasta que contém o checkout:
LLM_MODE=openai OPENAI_API_KEY_FILE=../.keys uv run python scripts/compare_modes.py
```

Cada comando executa um novo workflow. Não rodar as três alternativas em sala sem necessidade;
prepare a comparação antes e reserve oito minutos no bloco 10B. O script compara os objetos
Investigation e FinanceReport dos dois modos e imprime paridade; nenhuma mudança nas contas é aceita.
Sem chave a CLI termina com erro 2 antes de executar. Erro durante o grafo termina blocked/erro 1.
`smoke` e `doctor` verificam configuração/dados, sem chamada ao LLM; não comprovam acesso ao modelo.

## Exemplos e validação real

- [View mock](classroom/llm-decisions.txt): execução determinística real, cenário D, aprovação pendente.
- [View OpenAI real](examples/incident-001-openai-decisions.txt): gpt-4.1-mini, cenário D e aprovação pendente.
- [Comparação completa](examples/incident-001-modes-comparison.txt): duas execuções, paridade de evidências e cálculos.

Ensaio em 15/09/2026 após habilitação do modelo no projeto: seis respostas estruturadas reais,
`awaiting_approval`, `actions_executed=false`. Investigation e FinanceReport idênticos aos do mock.
Ambos escolheram D (R$ 12.500); essa coincidência não é garantia de que o LLM sempre escolha D.
Tempo observado para executar a comparação: 8,61 s, incluindo início do processo; não é benchmark.

A primeira tentativa recebeu HTTP 403 por falta de acesso ao modelo; o bloqueio está preservado
como [registro histórico](examples/incident-001-openai-blocked.txt), não como estado atual.
A validação real também detectou saída incompleta ao enviar o schema decimal original. O schema de
transporte foi simplificado para strings, preservando validação Money e conferência dos cálculos.
O exemplo acima foi gerado pelo fluxo completo após a correção, não pela montagem de etapas isoladas.

Fallback: mock ao vivo e exemplo OpenAI gravado, claramente identificado no material offline.
O texto do LLM pode variar e é consultivo. A suíte usa respostas controladas identificadas como testes;
o ensaio real está documentado separadamente e não é disparado por pytest.

## Referências da integração

[Structured Outputs com Pydantic](https://developers.openai.com/api/docs/guides/structured-outputs)
e [modelo GPT-4.1 mini](https://developers.openai.com/api/docs/models/gpt-4.1-mini).
