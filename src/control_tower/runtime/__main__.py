"""Entrypoint comum dos containers: python -m control_tower.runtime api|worker."""
import argparse
from .settings import RuntimeSettings
from .bootstrap import configure
from .store import CorrelatedStore
from ..telemetry.tracing import initialize_tracing


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('role', choices=['api', 'worker'])
    args = parser.parse_args()
    try:
        settings = RuntimeSettings()
        app = configure(settings)
        if settings.llm_mode == 'openai':
            from ..settings import Settings
            Settings.load(settings.control_tower_root)  # falha antes de aceitar jobs, sem request LLM
        if args.role == 'api':
            CorrelatedStore().initialize()  # idempotente; preserva dados e inicializa associação
            import uvicorn
            uvicorn.run('control_tower.api.app:create_app', factory=True,
                        host='0.0.0.0', port=8000, access_log=False)
        else:
            provider = initialize_tracing(settings)
            try:
                app.worker_main(['worker', '--pool=prefork',
                    f'--concurrency={settings.worker_concurrency}',
                    f'--hostname={settings.worker_name}@%h', '--loglevel=WARNING',
                    '--without-gossip', '--without-mingle'])
            finally:
                if provider:
                    provider.shutdown()
    except Exception as error:
        # Não imprimir DSN, chave nem representação de settings em falha de startup.
        raise SystemExit(f'Runtime não iniciou ({type(error).__name__}). '
                         'Verifique configuração, OPENAI_API_KEY se openai e dependências.') from None


if __name__ == '__main__':
    main()
