# Instruções de engenharia
Leia completamente docs/course/ antes de alterar código. PROJECT_CONTEXT.md é a fonte de requisitos.
Preserve decisões e checkpoints existentes; não mova tags aprovadas silenciosamente.
Escopo atual: lesson-01-start. Não implementar complete sem validação explícita do professor.
Um único sistema evolui nas quatro aulas; não criar quatro aplicações.
Python 3.12, uv, Pydantic; LangGraph/OpenAI na conclusão da Aula 1.
Use contratos tipados, módulos pequenos, Decimal para dinheiro e cálculos determinísticos.
Agentes acessam capabilities em tools, nunca CSVs diretamente. Aprovação humana permanece obrigatória.
Modo mock deve funcionar offline após instalação, sem chave e sem chamadas pagas.
Não adicione infraestrutura futura antes de surgir a necessidade didática.
Método: teoria → problema → demonstração → codificação conjunta → experimento → reflexão.
Execute uv run pytest e uv run control-tower smoke; confira README em ambiente limpo antes de tags.
Use commits pequenos e significativos. Nunca commite .env ou credenciais; se encontrar segredo,
pare e informe antes de publicar. Não publique mudanças sem solicitação.
Documente limites honestamente: este laboratório ensina engenharia de produção, não é produção real.
