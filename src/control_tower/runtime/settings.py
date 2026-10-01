"""Configuração do processo; a CLI histórica não passa por este bootstrap."""
import os
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from ..distributed.config import database_url, broker_url


class RuntimeSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore', hide_input_in_errors=True)

    # Aplicação e runtime
    app_env: Literal['local', 'test', 'production'] = 'local'
    app_name: str = 'control-tower'
    log_level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR'] = 'INFO'
    log_format: Literal['human', 'json'] = 'human'
    request_timeout: int = Field(default=3, ge=2, le=30)  # I/O de dependências, não duração do workflow
    worker_concurrency: int = Field(default=1, ge=1, le=16)
    worker_name: str = 'worker-a'
    control_tower_root: Path = Field(default_factory=Path.cwd)
    demo_controls_enabled: bool = False

    # Infra: nomes novos, aliases antigos; senhas nunca aparecem no repr.
    redis_url: SecretStr = Field(default_factory=lambda: SecretStr(broker_url()),
        validation_alias=AliasChoices('REDIS_URL', 'LESSON02_BROKER_URL'))
    database_url: SecretStr = Field(default_factory=lambda: SecretStr(database_url()),
        validation_alias=AliasChoices('DATABASE_URL', 'LESSON02_DATABASE_URL'))
    visibility_timeout: int = Field(default=900, ge=60,
        validation_alias=AliasChoices('VISIBILITY_TIMEOUT', 'LESSON02_VISIBILITY_TIMEOUT'))

    # LLM: a mesma configuração/validação da Aula 1 continua sendo a autoridade.
    llm_mode: Literal['mock', 'openai'] = 'mock'
    openai_model: str = 'gpt-4.1-mini'
    openai_api_key: SecretStr | None = None
    openai_api_key_file: str | None = None

    # Telemetria: desligada por padrão, sem exporter implícito.
    otel_capture_content: bool = False
    demo_agent_delay_ms: int = Field(default=0, ge=0, le=2000)
    otel_enabled: bool = False
    otel_service_name: str = 'control-tower'
    otel_exporter_otlp_endpoint: str | None = None

    @model_validator(mode='after')
    def coherent_runtime(self):
        if self.otel_capture_content:
            raise ValueError('Content capture não é suportado neste laboratório; use false')
        if self.demo_agent_delay_ms and not self.demo_controls_enabled:
            raise ValueError('Delay de agente exige DEMO_CONTROLS_ENABLED')
        if self.llm_mode == 'openai' and self.visibility_timeout < 600:
            raise ValueError('OpenAI exige VISIBILITY_TIMEOUT >= 600 em API e workers')
        if self.app_env == 'production' and self.demo_controls_enabled:
            raise ValueError('Controles didáticos não são permitidos em APP_ENV=production')
        return self

    def apply_legacy_environment(self):
        """Ponte explícita, executada uma vez antes de importar a aplicação Celery."""
        os.environ.update(
            LESSON02_BROKER_URL=self.redis_url.get_secret_value(),
            LESSON02_DATABASE_URL=self.database_url.get_secret_value(),
            LESSON02_VISIBILITY_TIMEOUT=str(self.visibility_timeout),
            CONTROL_TOWER_ROOT=str(self.control_tower_root.resolve()),
            LLM_MODE=self.llm_mode, OPENAI_MODEL=self.openai_model,
        )
        if self.openai_api_key:
            os.environ['OPENAI_API_KEY'] = self.openai_api_key.get_secret_value()
        if self.openai_api_key_file:
            os.environ['OPENAI_API_KEY_FILE'] = self.openai_api_key_file
