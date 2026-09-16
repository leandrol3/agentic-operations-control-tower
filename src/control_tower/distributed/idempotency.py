"""Identidade lógica estável; NÃO implementa deduplicação ou exactly-once."""
import hashlib
import json

from ..models import Contract
from .models import Text


class IdempotencyIdentity(Contract):
    incident_id: Text
    operation: Text = 'analyze-reference'
    version: Text = 'v1'

    @property
    def idempotency_key(self) -> str:
        # JSON evita colisões de concatenação: ('a:b','c') != ('a','b:c').
        canonical = json.dumps([self.incident_id, self.operation, self.version],
                               ensure_ascii=False, separators=(',', ':'))
        return 'idem-v1-' + hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def idempotency_key(incident_id: str, operation: str = 'analyze-reference', version: str = 'v1') -> str:
    return IdempotencyIdentity(incident_id=incident_id, operation=operation, version=version).idempotency_key
