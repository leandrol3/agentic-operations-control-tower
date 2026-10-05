# Segundo Cérebro — LAB NovaCore

MVP local: Markdown + YAML frontmatter + links relativos, um perfil inspirado em Open Knowledge
Format. OKF é tratado como formato, não plataforma nem certificação de compatibilidade com uma
especificação externa específica. Sem vector database, graph database ou ontologia completa.

`wiki/` guarda documentos e candidatos. `raw/executions/` guarda snapshots públicos sanitizados de
proveniência. `plans/` guarda planos propostos pelo Maestro. Git é usado manualmente para versionar;
nenhuma aprovação faz commit/push automático. Arquivos são escritos atomicamente com lock local.

Seeds approved são curadoria DIDÁTICA pré-preparada. Novos candidatos sempre pending_review.
Aprovação/rejeição exige nome, justificativa e confirmação humana. Não existe substituição automática
de documento aprovado, nem aprovação pelo Maestro/Compiler. Rejeitados não são usados no retrieval.

Este LAB não oferece IAM/RBAC, auditoria inviolável ou multi-tenancy. Use apenas localhost.
