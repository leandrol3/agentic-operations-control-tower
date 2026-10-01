"""A ajuda não depende de instalações opcionais; execução ausente orienta sem traceback."""
import subprocess
import sys
import pytest

# Processo novo impede imports prévios de esconder a regressão, mesmo com extras instalados.
BLOCK_OPTIONALS = '''
import importlib.abc, sys
class WithoutExtras(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'psycopg', 'celery', 'kombu', 'redis'}:
            raise ModuleNotFoundError('optional dependency unavailable', name=fullname.split('.')[0])
sys.meta_path.insert(0, WithoutExtras())
from control_tower.main import main
main()
'''


@pytest.mark.parametrize('command',['db-init','enqueue','executions','execution','events','result'])
def test_help_without_optional_dependencies(command):
    result=subprocess.run([sys.executable,'-c',BLOCK_OPTIONALS,command,'--help'],text=True,capture_output=True)
    assert result.returncode==0,result.stderr
    assert 'usage:' in result.stdout and 'Traceback' not in result.stderr


@pytest.mark.parametrize('command',['db-init','enqueue','executions'])
def test_execution_without_extras_has_actionable_error(command):
    result=subprocess.run([sys.executable,'-c',BLOCK_OPTIONALS,command],text=True,capture_output=True)
    assert result.returncode==2
    assert 'uv sync --extra lesson02' in result.stderr
    assert 'Traceback' not in result.stderr
