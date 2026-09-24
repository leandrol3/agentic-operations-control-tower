"""Um artefato, papéis distintos. Configurar antes de importar o app Celery."""
from .settings import RuntimeSettings
from ..telemetry.logging import configure_logging


def configure(settings: RuntimeSettings):
    settings.apply_legacy_environment()
    configure_logging(settings.otel_service_name, settings.log_format, settings.log_level)
    from ..distributed.celery_app import app
    # Mantém ack/retry/prefetch/queue originais. Só endereços e timeout por ambiente.
    app.conf.update(broker_url=settings.redis_url.get_secret_value(),
        broker_connection_timeout=settings.request_timeout,
        broker_transport_options={'visibility_timeout': settings.visibility_timeout,
                                  'socket_connect_timeout': settings.request_timeout,
                                  'socket_timeout': settings.request_timeout},
        visibility_timeout=settings.visibility_timeout)
    from .signals import install_signals
    install_signals()
    return app
