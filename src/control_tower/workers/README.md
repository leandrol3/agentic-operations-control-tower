# Workers Celery reais

Um processo solo por terminal é a configuração didática portátil, inclusive macOS. Usar Celery padrão:

```bash
uv run celery -A control_tower.distributed.celery_app worker --pool=solo --concurrency=1 --hostname='lesson02-A@%h' --loglevel=INFO --without-gossip --without-mingle
```

No segundo terminal trocar A por B. O workflow ainda possui seu paralelismo interno de especialistas.
Não existe container de aplicação. SIGKILL do worker inteiro exige visibility timeout Redis para
redelivery; não confundir com perda de filho prefork enquanto pai Celery permanece vivo.
Ver procedimento completo e fallback no runbook. Não matar processos por padrões amplos de nome.
