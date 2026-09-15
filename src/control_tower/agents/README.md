# Papéis em modo mock

- supervisor.py: plano explícito para INCIDENT-001 e consolidação de evidências.
- specialists.py: Supply, Production e Logistics, cada um com tools e saída tipada.
- finance.py: comparação A–D via scenarios.py; propõe menor custo incremental.
- challenger.py: verifica consistência, políticas, premissas e informação insuficiente;
  seleciona o menor custo admissível, que pode diferir da proposta de Finance.

São papéis determinísticos do mock, não raciocínio de LLM. Não leem CSVs diretamente nem executam ações.
O professor demonstra as responsabilidades; alunos observam e reproduzem posteriormente.
Ver [runbook](../../../docs/course/lesson-01-runbook.md).
