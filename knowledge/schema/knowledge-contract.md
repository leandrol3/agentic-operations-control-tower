# Contrato de conhecimento

Metadata: id, type (entity/decision/lesson/pattern), title, summary, tags, source_execution,
source_incident, source (didactic/durable), evidence (id/text/source), related, validation_status,
created_at, updated_at, generated_by, owner, provenance, evidence_level, reviewer, review_note.

Estados: draft, pending_review, approved, rejected, superseded. Compiler só cria pending_review;
a UI permite pending_review → approved/rejected mediante confirmação humana. Outros estados estão
no formato para evolução; não há transições automáticas. Conteúdo é Markdown, tratado como texto
não confiável: a UI não renderiza HTML arbitrário.

Fonte de execução e evidências são vinculadas pelo backend, não escolhidas pelo modelo.
IDs citados precisam existir no contexto. Relações geradas devem apontar a itens aprovados da mesma
fonte. Schema e proveniência são validados automaticamente; verdade semântica requer revisão humana.
Observações fornecidas são reproduzidas literalmente. Inferência do modelo é rotulada como proposta.
