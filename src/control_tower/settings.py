"""Configuração local. Mock não lê credenciais nem importa o SDK OpenAI."""
from dataclasses import dataclass, field
import os
from pathlib import Path


def read_env(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    values = {}
    for line in path.read_text().splitlines():
        key, sep, value = line.strip().removeprefix('export ').partition('=')
        if sep and not key.startswith('#'):
            values[key.strip()] = value.strip().strip('\"\'')
    return values


@dataclass(frozen=True)
class Settings:
    mode: str = 'mock'
    model: str = 'gpt-4.1-mini'
    api_key: str = field(default='', repr=False)

    @classmethod
    def load(cls, root: Path):
        env = read_env(root / '.env') | dict(os.environ)
        mode = env.get('LLM_MODE', 'mock')
        if mode not in ('mock', 'openai'):
            raise ValueError('LLM_MODE deve ser mock ou openai')
        if mode == 'mock':
            return cls()
        key = env.get('OPENAI_API_KEY', '').strip()
        if not key:
            path = Path(env.get('OPENAI_API_KEY_FILE', '.keys'))
            if not path.is_absolute():
                path = root / path
            if path.is_file():
                values = read_env(path)
                key = values.get('OPENAI_API_KEY', '')
                if not key:
                    raw = path.read_text().strip()
                    key = raw if raw.startswith('sk-') and '\n' not in raw else ''
        if not key:
            raise ValueError('LLM_MODE=openai requer OPENAI_API_KEY (ambiente, .env ou arquivo .keys)')
        model = env.get('OPENAI_MODEL', 'gpt-4.1-mini').strip()
        if not model:
            raise ValueError('OPENAI_MODEL não pode ser vazio')
        return cls(mode, model, key)

    def interpreter(self):
        if self.mode == 'mock':
            return None
        from .llm import OpenAIInterpreter
        return OpenAIInterpreter(self.api_key, self.model)
