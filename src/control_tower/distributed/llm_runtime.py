"""Fronteira operacional mínima; reutiliza prompts/contratos da Aula 1.

Retry é por request (uma repetição). Falha propagada decide continuidade fora do
LangGraph, sem outro grafo, provider obrigatório, custo ou tracing.
"""
from copy import copy
from types import SimpleNamespace
import time
from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAIError
from ..llm import OpenAIInterpreter
from ..settings import Settings
from .config import project_root, visibility_timeout


class ProviderUnavailable(RuntimeError):
    def __init__(self, reason, transient):
        super().__init__(reason)
        self.transient = transient


def settings_for(options):
    # Mock é independente das credenciais, mesmo em ambiente de teste.
    if options.llm_mode == 'mock':
        return Settings()
    settings = Settings.load(project_root())
    if settings.mode != 'openai':
        raise ValueError('Task openai exige worker iniciado com LLM_MODE=openai e OPENAI_API_KEY')
    if settings.model != options.llm_model:
        raise ValueError('OPENAI_MODEL do worker difere do modelo persistido pelo producer')
    if visibility_timeout() < 600:
        raise ValueError('Demo OpenAI exige LESSON02_VISIBILITY_TIMEOUT >= 600 em producer e workers')
    return settings


class ResilientInterpreter:
    def __init__(self, settings, session, options, *, client=None, sleep=time.sleep):
        self.model = settings.model
        self.base = OpenAIInterpreter(settings.api_key, settings.model, client=client)
        self.session, self.options, self.sleep = session, options, sleep

    def parse(self, role, schema, context):
        # Proxy por chamada: especialistas paralelos nunca compartilham role mutável.
        interpreter = copy(self.base)
        interpreter.client = SimpleNamespace(responses=SimpleNamespace(
            parse=lambda **kwargs: self.request(role, **kwargs)))
        try:
            return interpreter.parse(role, schema, context)
        except ValueError:
            self.session.event('llm.failed', role, detail='invalid_structured_response')
            raise ProviderUnavailable('invalid_structured_response', False) from None

    def request(self, role, **kwargs):
        for request_attempt in (1, 2):
            self.session.event('llm.requested', role, detail=f'provider=openai request_attempt={request_attempt}')
            started = time.perf_counter()
            try:
                if self.options.llm_failure == 'timeout':
                    raise ProviderUnavailable('simulated_timeout', True)
                response = self.base.client.responses.parse(**kwargs)
            except (ProviderUnavailable, OpenAIError) as error:
                if isinstance(error, ProviderUnavailable):
                    reason, transient = str(error), error.transient
                elif isinstance(error, (APITimeoutError, APIConnectionError)):
                    reason, transient = type(error).__name__, True
                elif isinstance(error, APIStatusError):
                    reason = f'http_{error.status_code}'
                    transient = error.status_code in (408, 429) or error.status_code >= 500
                else:
                    reason, transient = type(error).__name__, False
                self.session.event('llm.failed', role, detail=reason,
                                   duration_ms=(time.perf_counter()-started)*1000)
                if transient and request_attempt == 1:
                    self.session.event('llm.retry', role, detail='Mesma capacidade; uma repetição após 1 segundo')
                    self.sleep(1)
                    continue
                raise ProviderUnavailable(reason, transient) from None
            usage = getattr(response, 'usage', None)
            self.session.event('llm.completed', role, duration_ms=(time.perf_counter()-started)*1000,
                input_tokens=getattr(usage, 'input_tokens', None), output_tokens=getattr(usage, 'output_tokens', None))
            return response
