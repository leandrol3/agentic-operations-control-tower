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
