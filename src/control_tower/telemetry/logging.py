"""Logs allowlist: nenhum payload, prompt, credencial ou exceção bruta."""
from datetime import datetime, timezone
import json
import logging
import sys
from .context import current_context

LOGGER = logging.getLogger('control_tower.runtime')


class ContextFormatter(logging.Formatter):
    def __init__(self, service: str, log_format: str):
        super().__init__()
        self.service, self.log_format = service, log_format

    def format(self, record):
        context = getattr(record, 'execution_context', None)
        row = dict(timestamp=datetime.now(timezone.utc).isoformat(), level=record.levelname,
                   service=self.service, execution_id=None, incident_id=None, trace_id=None,
                   correlation_id=None, worker_id=None)
        if context:
            row.update(context.model_dump(mode='json'))
        row.update(event=getattr(record, 'event', 'runtime.log'), message=record.getMessage())
        row.update(getattr(record, 'safe_fields', {}))
        if self.log_format == 'json':
            return json.dumps(row, ensure_ascii=False)
        return ' | '.join(f'{key}={value}' for key, value in row.items() if value is not None)


def configure_logging(service: str, log_format='human', level='INFO'):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ContextFormatter(service, log_format))
    LOGGER.handlers[:] = [handler]
    LOGGER.propagate = False
    LOGGER.setLevel(level)


def log_event(event: str, message: str, *, level=logging.INFO, **safe_fields):
    LOGGER.log(level, message, extra={'event': event, 'execution_context': current_context.get(),
                                    'safe_fields': safe_fields})
