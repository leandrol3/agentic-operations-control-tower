"""Sondas limitadas de Redis/PostgreSQL. Nenhuma consulta a LLM ou workers."""
import psycopg
import redis


def postgres_ready(settings):
    try:
        with psycopg.connect(settings.database_url.get_secret_value(),
                connect_timeout=settings.request_timeout,
                options=f'-c statement_timeout={settings.request_timeout * 1000}') as conn:
            # Não só TCP: tabelas esperadas precisam existir para aceitar trabalho.
            row = conn.execute("SELECT to_regclass('ct_executions'), to_regclass('ct_events'), "
                               "to_regclass('ct_execution_context')").fetchone()
            return all(row)
    except psycopg.Error:
        return False


def redis_ready(settings):
    try:
        with redis.Redis.from_url(settings.redis_url.get_secret_value(),
                socket_connect_timeout=settings.request_timeout,
                socket_timeout=settings.request_timeout, retry_on_timeout=False) as client:
            return bool(client.ping())
    except redis.RedisError:
        return False


def check_readiness(settings):
    return {'redis': 'ok' if redis_ready(settings) else 'unavailable',
            'postgres': 'ok' if postgres_ready(settings) else 'unavailable'}
