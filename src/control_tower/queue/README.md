# Queue Redis/Celery

Celery/Kombu implementa entrega; não criamos uma fila própria. Queue `lesson02`, Redis DB 2 por padrão.
Producer: `distributed/producer.py`. Configuração: `distributed/celery_app.py`.
Late ack + prefetch 1 limitam reserva de trabalho, mas não limitam admissão do producer.
Mensagens incluem envelope, execution_id e idempotency_key. PostgreSQL protege identidade e
processamento; resultado Celery é ignorado. At-least-once delivery + idempotent processing.
Não usar purge/flush para reiniciar uma demo: escolher nova version preserva o histórico.
