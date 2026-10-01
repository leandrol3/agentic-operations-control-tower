"""Ping direcionado: consumidor responde via broker; não testa o workflow."""
import socket
from .settings import RuntimeSettings
from .bootstrap import configure

if __name__ == '__main__':
    settings = RuntimeSettings()
    app = configure(settings)
    destination = f'{settings.worker_name}@{socket.gethostname()}'
    try:
        replies = app.control.ping(destination=[destination], timeout=3)
        raise SystemExit(0 if any(reply.get(destination, {}).get('ok') == 'pong' for reply in replies) else 1)
    except Exception:
        raise SystemExit(1) from None
