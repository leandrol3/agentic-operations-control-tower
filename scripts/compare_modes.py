"""Comparação real de duas execuções; não troca OpenAI por mock silenciosamente."""
from pathlib import Path
import sys

from control_tower.graph.workflow import run_workflow
from control_tower.settings import Settings
from control_tower.tools import Tools
from control_tower.views import render_view


def main():
    root = Path(__file__).resolve().parents[1]
    settings = Settings.load(root)
    if settings.mode != 'openai':
        raise ValueError('Use LLM_MODE=openai para comparar mock com a API real')
    tools = Tools(root)
    incident = tools.load_incident(root / 'incidents/incident_001.json')
    mock = run_workflow(tools, incident)
    print(render_view(mock, 'llm-decisions', tools), flush=True)
    live = run_workflow(tools, incident, llm=settings.interpreter())
    print('\n' + render_view(live, 'llm-decisions', tools), flush=True)
    if live.status == 'blocked':
        print('OpenAI bloqueado: comparação de cálculos não concluída. Mock disponível para aula.')
        return 1
    same_evidence = mock.investigation == live.investigation
    same_finance = mock.finance == live.finance
    print(f'PARIDADE | mesma evidência: {same_evidence} | mesmos cálculos A–D: {same_finance}')
    print('Escolhas finais podem diferir entre cenários admissíveis; contas de cada cenário não mudam.')
    return 0 if same_evidence and same_finance else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(2)
