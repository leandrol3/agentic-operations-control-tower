"""Configuração local explícita; não lê .keys nem ativa chamadas a LLM."""
import os
from pathlib import Path
from urllib.parse import quote


def database_url():
    return os.getenv('LESSON02_DATABASE_URL') or (
        'postgresql://novacore:' + quote(os.getenv('LESSON02_POSTGRES_PASSWORD', 'novacore_demo_only'), safe='')
        + '@127.0.0.1:' + os.getenv('LESSON02_POSTGRES_PORT', '15432') + '/novacore')


def broker_url():
    return os.getenv('LESSON02_BROKER_URL', 'redis://127.0.0.1:' + os.getenv('LESSON02_REDIS_PORT', '16379') + '/2')


def project_root():
    return Path(os.getenv('CONTROL_TOWER_ROOT', str(Path.cwd()))).resolve()

MAX_ATTEMPTS = 3
VISIBILITY_TIMEOUT = 60  # didático; workflow mock + delay <=30 s, não usar para LLM lento
QUEUE = 'lesson02'


def visibility_timeout():
    value = int(os.getenv('LESSON02_VISIBILITY_TIMEOUT', '900' if os.getenv('LLM_MODE') == 'openai' else '60'))
    if value < 60:
        raise ValueError('LESSON02_VISIBILITY_TIMEOUT deve ser >= 60')
    return value
